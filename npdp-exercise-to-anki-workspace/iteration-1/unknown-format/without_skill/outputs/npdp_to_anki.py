# -*- coding: utf-8 -*-
"""把 NPDP 题库 markdown 转成 Anki「选择题」模板可导入的 TSV。

支持两种来源格式，按题号行的写法自动认：

**章节题库**（docs/npdp/exercise/*.md）：

    1、 [单选] 题干……
     A：选项一
     B：选项二
     C：选项三
     D：选项四
    正确答案：B 你的答案：D
    解析：①考点提炼……
    ②正确答案解析……
    ③其他答案不正确解析：
    A. ……
    C. ……
    D. ……
    ④考点延展……

**模拟题**（docs/npdp/mock/*.md）：

    **1.** 题干……（多选）

    A. 选项一
    B. 选项二

    答案：AC

    解析：一段散文式解析，没有 ①②③④ 分节，也没有逐选项解析。

两者的差别落在字段上：章节题库的解析能拆出 ③，于是 noteA…noteF 有内容；
模拟题只有一整段解析，noteA…noteF 全空，也就没有 `.fixes.md` 的必要。

本模块只做「解析 → 17 个字段」的确定性转换。遇到解析结构与答案对不上时
抛 ParseError 而不是猜——静默产出错数据比报错危险得多。
"""

import pathlib
import re
import sys
from dataclasses import dataclass

# 模板支持的选项上限（templates/mcq/README.md）
LETTERS = "ABCDEF"

# Anki 笔记类型「NPDP 选择题」的字段顺序，即 TSV 的列顺序
FIELD_ORDER = (
    "id", "question",
    "optionA", "optionB", "optionC", "optionD", "optionE", "optionF",
    "answer", "note",
    "noteA", "noteB", "noteC", "noteD", "noteE", "noteF",
    "source",
)

_Q_RE = re.compile(r"^(\d+)、\s*\[(单选|多选)\]\s*(.*)$")
_OPT_RE = re.compile(r"^ ([A-F])：\s*(.*)$")
_ANS_RE = re.compile(r"^正确答案：([A-F]+)\s+你的答案：([A-F]+)\s*$")

# 模拟题格式：**1.** 题号行 / `A. 选项` / `答案：AC` / `解析：` 散文，
# 题与题之间用 --- 分隔。详见模块 docstring。
_MOCK_Q_RE = re.compile(r"^\*\*(\d+)\.\*\*\s*(.*)$")
_MOCK_OPT_RE = re.compile(r"^([A-F])\.\s*(.*)$")
_MOCK_ANS_RE = re.compile(r"^答案：([A-F]+)\s*$")
_MOCK_MULTI_RE = re.compile(r"\s*[（(]多选[）)]")
_MOCK_NOTE_PREFIX = "解析："
_RULE_RE = re.compile(r"^-{3,}\s*$")


class ParseError(Exception):
    """题库格式不符合预期。"""


@dataclass
class Question:
    no: int
    kind: str          # 单选 / 多选
    stem: str
    options: dict      # {"A": "选项一", ...}
    answer: str        # "B" / "AC"
    note_raw: str      # 「解析：」之后的全部原文
    fmt: str = "chapter"   # chapter = 章节题库，mock = 模拟题


def _parse_block(block):
    head = _Q_RE.match(block[0])
    q = Question(no=int(head.group(1)), kind=head.group(2), stem=head.group(3),
                 options={}, answer="", note_raw="")

    note = []
    in_note = False
    for line in block[1:]:
        if in_note:
            note.append(line)
        elif line.startswith("解析："):
            in_note = True
            note.append(line[len("解析："):])
        else:
            m = _OPT_RE.match(line)
            if m:
                q.options[m.group(1)] = m.group(2)
                continue
            m = _ANS_RE.match(line)
            if m:
                q.answer = m.group(1)

    q.note_raw = "\n".join(note).strip("\n")
    return q


# ---- 模拟题格式 --------------------------------------------------------

def _parse_mock_block(block):
    """`**1.** 题干（多选）` + `A. 选项` + `答案：AC` + `解析：散文` → Question。

    题干里的「（多选）」是格式标记，不是题干内容，剥掉——笔记类型由
    `answer` 的长度自己判多选（templates/mcq/README.md），留着会重复显示。
    """
    head = _MOCK_Q_RE.match(block[0])
    marked = bool(_MOCK_MULTI_RE.search(head.group(2)))
    q = Question(no=int(head.group(1)),
                 kind="多选" if marked else "单选",
                 stem=_MOCK_MULTI_RE.sub("", head.group(2)).strip(),
                 options={}, answer="", note_raw="", fmt="mock")

    note = []
    in_note = False
    for line in block[1:]:
        # 题与题之间的 --- 既不是题干也不是解析
        if _RULE_RE.match(line):
            break
        if in_note:
            note.append(line)
            continue
        if line.startswith(_MOCK_NOTE_PREFIX):
            in_note = True
            note.append(line[len(_MOCK_NOTE_PREFIX):])
            continue
        if not line.strip():
            continue
        m = _MOCK_OPT_RE.match(line)
        if m:
            q.options[m.group(1)] = m.group(2).strip()
            continue
        m = _MOCK_ANS_RE.match(line)
        if m:
            q.answer = m.group(1)
            continue
        # 题干换行、粘进来的表格、别的东西 —— 与其悄悄吞掉，不如报出来
        raise ParseError(f"Q{q.no} 里有无法识别的行：{line[:40]!r}")

    q.note_raw = "\n".join(note).strip("\n")
    _check_mock(q, marked)
    return q


def _check_mock(q, marked):
    """模拟题的完整性自检——缺件、字母不连续、答案不在选项里，都直接停手。

    最后一条（「（多选）」标记与答案长度必须一致）是在抓答案键漏字母：
    题干说多选、答案却只有一个字母，多半是漏抄了，猜不出来就报错。
    """
    if not q.stem:
        raise ParseError(f"Q{q.no} 没有题干")
    if not q.options:
        raise ParseError(f"Q{q.no} 没有选项")
    got = sorted(q.options)
    want = list(LETTERS[:len(got)])
    if got != want:
        raise ParseError(f"Q{q.no} 的选项字母是 {got}，应该是连续的 {want}")
    if not q.answer:
        raise ParseError(f"Q{q.no} 没有「答案：」行")
    stray = sorted(set(q.answer) - set(q.options))
    if stray:
        raise ParseError(f"Q{q.no} 的答案里有不存在的选项 {stray}")
    if (len(q.answer) > 1) != marked:
        raise ParseError(
            f"Q{q.no} 的答案 {q.answer} 是 {'多选' if len(q.answer) > 1 else '单选'}，"
            f"但题干里{'没有' if marked else '有'}「（多选）」标记")
    if not q.note_raw:
        raise ParseError(f"Q{q.no} 没有「解析：」内容")


# ---- 格式识别 ----------------------------------------------------------

_PATTERNS = {"chapter": _Q_RE, "mock": _MOCK_Q_RE}
_BLOCK_PARSERS = {"chapter": _parse_block, "mock": _parse_mock_block}
# 顺序即优先级：先试章节题库（老格式），再试模拟题
_FORMAT_ORDER = ("chapter", "mock")


def detect_format(text):
    """按题号行的写法认格式。认不出就报错——绝不返回零道题。"""
    lines = text.split("\n")
    for name in _FORMAT_ORDER:
        if any(_PATTERNS[name].match(l) for l in lines):
            return name
    raise ParseError(
        "认不出这份题库的格式：既没有「1、 [单选]」开头的题号行，"
        "也没有「**1.**」开头的题号行")


def parse_questions(text, fmt=None):
    """把整份题库 markdown 切成 Question 列表。fmt 缺省时自动识别。"""
    fmt = fmt or detect_format(text)
    pattern = _PATTERNS[fmt]
    parse = _BLOCK_PARSERS[fmt]
    lines = text.split("\n")
    starts = [i for i, l in enumerate(lines) if pattern.match(l)]
    starts.append(len(lines))
    return [parse(lines[starts[k]:starts[k + 1]])
            for k in range(len(starts) - 1)]


# ---- 解析原文的拆分 ----------------------------------------------------

_MARKERS = ("①", "②", "③", "④")
_SECTIONS = ("concept", "answer", "others", "extension")
# 每段开头的小标题，如「该题目考察的考点提炼：」「其他答案不正确解析：」
_TITLE_RE = re.compile(r"^[^：\n]*：\s*")
_OTHER_ITEM_RE = re.compile(r"^([A-F])\.\s*(.*)$")


def split_note(note_raw):
    """把「解析：」原文拆成 concept / answer / others / extension 四段。

    每段剥掉开头的小标题（「考点延展：」之类），调用方要标题就自己加。
    """
    pos = []
    for mk in _MARKERS:
        i = note_raw.find(mk)
        if i == -1:
            raise ParseError(f"解析缺少 {mk} 段：{note_raw[:40]!r}")
        pos.append(i)
    if pos != sorted(pos):
        raise ParseError("解析中 ①②③④ 的顺序不对")

    bounds = pos + [len(note_raw)]
    out = {}
    for k, name in enumerate(_SECTIONS):
        body = note_raw[bounds[k] + 1:bounds[k + 1]].strip("\n")
        out[name] = _TITLE_RE.sub("", body, count=1).strip()
    return out


def parse_others(others_body, wrong_letters, no=None):
    """③ 逐选项解析 → {字母: 解析}。

    只接受「A. 解析」一行一条的形式。条目字母与 `wrong_letters` 对不上、
    或出现合并成一行 / 跨行的内容时抛 ParseError —— 这两种情况都意味着
    题库原文有问题，猜一个结果出来会让卡片悄悄带上错解析。
    """
    where = f"Q{no} " if no is not None else ""
    items = {}
    for raw in others_body.split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = _OTHER_ITEM_RE.match(line)
        if not m:
            raise ParseError(
                f"{where}③ 里有无法识别的行（合并写的选项或拍平的表格）：{line[:40]!r}")
        letter = m.group(1)
        if letter in items:
            raise ParseError(f"{where}③ 里 {letter} 出现了两次")
        items[letter] = m.group(2).strip()

    got, want = sorted(items), sorted(wrong_letters)
    if got != want:
        raise ParseError(f"{where}③ 拆到的字母是 {got}，但错误选项应为 {want}")
    return items


def extension_needs_fix(extension_body):
    """④ 里含空行 → 是被拍平的表格（单元格之间原本就有空行），需人工整理。"""
    return any(not line.strip() for line in extension_body.split("\n"))


# ---- 修复文件 ----------------------------------------------------------

_FIX_HEAD_RE = re.compile(r"^##\s*(\d+)\s*·\s*([a-z_]+)\s*$")
# 二级标题或水平分隔线都结束当前段落 —— 否则文件末尾的「## 手工去重」
# 和它前面的 --- 会被悄悄拼进上一段，变成卡片上的垃圾。
_FIX_BOUNDARY_RE = re.compile(r"^(?:##|-{3,})")


def load_fixes(path):
    """读 chapter-N.fixes.md → {题号: {段落名: 替代文本}}。

    段落用「## 题号 · 段落名」开头，正文到下一个标题为止；正文为空即置空。
    """
    text = pathlib.Path(path).read_text(encoding="utf-8")
    out = {}
    cur = None
    buf = []

    def flush():
        if cur is not None:
            out.setdefault(cur[0], {})[cur[1]] = "\n".join(buf).strip()

    for line in text.split("\n"):
        m = _FIX_HEAD_RE.match(line)
        if m:
            flush()
            cur = (int(m.group(1)), m.group(2))
            buf = []
        elif _FIX_BOUNDARY_RE.match(line):
            flush()
            cur = None
            buf = []
        elif cur is not None:
            buf.append(line)
    flush()
    return out


_DUPE_HEAD = "## 手工去重"
_DUPE_RE = re.compile(r"^(\d+)\s*(?:→|->)\s*(\d+)\s*$")


def load_manual_dupes(path):
    """读修复文件里的「## 手工去重」段 → {丢掉的题号: 保留的题号}。

    自动去重靠题干逐字相等，抓不到「哪类客户采用群体／哪个客户采用类别」这种
    同一道题的两种措辞，所以留一份手工清单。
    """
    text = pathlib.Path(path).read_text(encoding="utf-8")
    out = {}
    inside = False
    for line in text.split("\n"):
        if line.startswith("##"):
            inside = line.strip() == _DUPE_HEAD
            continue
        if inside:
            m = _DUPE_RE.match(line.strip())
            if m:
                out[int(m.group(1))] = int(m.group(2))
    return out


# ---- 去重 --------------------------------------------------------------

def dedupe(questions, manual=None):
    """去重，保留首次出现的题号。

    自动部分按「题干 + 选项 + 答案」逐字比对；`manual` 里的题号
    （{丢掉的题号: 保留的题号}）直接丢掉，用于抓近似重复。

    返回 (留下的题, [(被丢掉的题号, 保留的题号), ...])。
    """
    manual = dict(manual or {})
    seen = {}
    kept = []
    dropped = []
    for q in questions:
        if q.no in manual:
            dropped.append((q.no, manual[q.no]))
            continue
        key = (q.stem, tuple(sorted(q.options.items())), q.answer)
        if key in seen:
            dropped.append((q.no, seen[key]))
        else:
            seen[key] = q.no
            kept.append(q)
    return kept, dropped


# ---- 字段构造 ----------------------------------------------------------

_ARROW_RE = re.compile(r"\s+->\s+")


def to_field(text):
    """转成 Anki 字段内容：换行 → <br>，HTML 特殊字符转义。

    字段是 HTML，题库里的 `<5%` 不转义会被当成标签吃掉。
    先转义再插 <br>，否则自己插的 <br> 也会被转义掉。
    """
    s = _ARROW_RE.sub(" → ", text)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s.replace("\n", "<br>")


def _note_text(sec, ext_body, extra):
    """note 字段 = ①考点提炼 + ②正确答案解析 + ④考点延展 (+ 补充)。"""
    parts = ["考点提炼：" + sec["concept"], "正确答案解析：" + sec["answer"]]
    if ext_body:
        parts.append("考点延展：" + ext_body)
    if extra:
        parts.append(extra)
    return "\n".join(parts)


def build_row(q, chapter, fixes, source_label=None):
    """一道题 → 一个 {字段名: 值} 字典，键的顺序即 FIELD_ORDER。

    `chapter` 是来源标识，只进 id：章节题库传章节号（`1` → `npdp-1-003`），
    模拟题传文件名 stem（`mock-exam-1` → `npdp-mock-exam-1-003`）。
    `source_label` 是 source 字段的内容，缺省时按章节号拼「第N章」。
    """
    if q.fmt == "mock":
        return _build_mock_row(q, chapter, fixes, source_label)
    return _build_chapter_row(q, chapter, fixes, source_label)


def _build_mock_row(q, chapter, fixes, source_label):
    """模拟题：只有一整段解析 → note，没有逐选项解析 → noteA…noteF 全空。

    模拟题不带 `.fixes.md`，但沿用同一套修复文件读取，`note_extra` 仍可用。
    """
    note = "\n".join(x for x in (q.note_raw, fixes.get(q.no, {}).get("note_extra", ""))
                     if x)
    row = {
        "id": f"npdp-{chapter}-{q.no:03d}",
        "question": q.stem,
        "answer": q.answer,
        "note": note,
        "source": source_label or str(chapter),
    }
    for letter in LETTERS:
        row["option" + letter] = q.options.get(letter, "")
        row["note" + letter] = ""

    return {name: to_field(row[name]) for name in FIELD_ORDER}


def _build_chapter_row(q, chapter, fixes, source_label=None):
    fix = fixes.get(q.no, {})
    sec = split_note(q.note_raw)

    others_body = fix.get("others", sec["others"])
    ext_body = fix.get("extension", sec["extension"])

    wrong = sorted(set(q.options) - set(q.answer))
    notes = parse_others(others_body, wrong, no=q.no) if others_body.strip() else {}

    row = {
        "id": f"npdp-{chapter}-{q.no:03d}",
        "question": q.stem,
        "answer": q.answer,
        "note": _note_text(sec, ext_body, fix.get("note_extra", "")),
        "source": source_label or f"第{chapter}章",
    }
    for letter in LETTERS:
        row["option" + letter] = q.options.get(letter, "")
        row["note" + letter] = notes.get(letter, "")

    return {name: to_field(row[name]) for name in FIELD_ORDER}


def to_tsv(rows):
    """Anki「导入文件」用的 TSV：制表符分列，一行一张卡。"""
    return "".join(
        "\t".join(row[name] for name in FIELD_ORDER) + "\n" for row in rows)


def convert(text, chapter, fixes, manual=None, source_label=None, fmt=None):
    """题库 markdown → TSV 行列表（已去重）。格式缺省时自动识别。"""
    kept, _dropped = dedupe(parse_questions(text, fmt), manual)
    return [build_row(q, chapter, fixes, source_label) for q in kept]


# ---- 命令行 ------------------------------------------------------------

_CHAPTER_IN_NAME_RE = re.compile(r"chapter-(\d+)")
_H1_RE = re.compile(r"^#\s+(.+?)\s*$")


def chapter_of(md_path):
    """docs/npdp/exercise/chapter-1.md → 1"""
    m = _CHAPTER_IN_NAME_RE.search(pathlib.Path(md_path).stem)
    if not m:
        raise ParseError(f"文件名里找不到章节号：{md_path}")
    return int(m.group(1))


def _h1_title(text):
    """文档的一级标题，没有则返回空串。`## 二级标题` 不会被误当成 H1。"""
    for line in text.split("\n"):
        m = _H1_RE.match(line)
        if m:
            return m.group(1)
    return ""


def source_of(md_path, text, fmt):
    """→ (id 前缀, source 字段)。

    章节题库：文件名里的 `chapter-N` 是章节号 → (`1`, `第1章`)。
    模拟题：文件名 stem 当 id 前缀、一级标题当来源 —— 所以**改文件名会让
    重导入多出一份卡片**，id 变了。

    内容和文件名对不上时报错：一份模拟题存成 `chapter-1.md` 会拿到
    `npdp-1-*` 的 id，和真正的第 1 章撞车，那是要覆盖掉已有卡片的。
    """
    stem = pathlib.Path(md_path).stem
    m = _CHAPTER_IN_NAME_RE.search(stem)
    if fmt == "mock":
        if m:
            raise ParseError(
                f"{md_path} 的内容是模拟题格式，文件名却带章节号 chapter-"
                f"{m.group(1)}——id 会和第 {m.group(1)} 章撞车，请改成"
                f"不带章节号的文件名")
        return stem, _h1_title(text) or stem
    if not m:
        raise ParseError(f"文件名里找不到章节号：{md_path}")
    n = int(m.group(1))
    return str(n), f"第{n}章"


def run(md_path):
    """读题库 md 与同名 .fixes.md，返回 (TSV 文本, 行列表)。"""
    md_path = pathlib.Path(md_path)
    fixes_path = md_path.with_name(md_path.stem + ".fixes.md")
    has_fixes = fixes_path.exists()
    fixes = load_fixes(fixes_path) if has_fixes else {}
    manual = load_manual_dupes(fixes_path) if has_fixes else {}
    text = md_path.read_text(encoding="utf-8")
    fmt = detect_format(text)
    key, label = source_of(md_path, text, fmt)
    rows = convert(text, chapter=key, fixes=fixes, manual=manual,
                   source_label=label, fmt=fmt)
    return to_tsv(rows), rows


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print("用法：python scripts/npdp_to_anki.py <题库.md>", file=sys.stderr)
        return 2

    md_path = pathlib.Path(argv[0])
    tsv_path = md_path.with_suffix(".tsv")
    try:
        tsv, rows = run(md_path)
    except ParseError as e:
        print(f"题库格式有问题，已停手：{e}", file=sys.stderr)
        return 1

    tsv_path.write_text(tsv, encoding="utf-8")
    print(f"{md_path} → {tsv_path}：{len(rows)} 题")
    return 0


if __name__ == "__main__":
    sys.exit(main())
