# -*- coding: utf-8 -*-
"""
chapter-1.md  →  Anki「NPDP 选择题」可导入的 TSV

字段顺序（见 templates/mcq/README.md）：
  id, question, optionA..optionF, answer, note, noteA..noteF, source

用法:  python npdp_to_anki.py <chapter-N.md> [输出.tsv]
零依赖，只用标准库。
"""
import re
import sys
import collections
import difflib

# ---------------------------------------------------------------- 常量

CHAPTER = "第1章"
Q_START = re.compile(r"^(\d+)、\s*\[(单选|多选|不定项)\]\s*(.*)$")
OPT = re.compile(r"^\s*([A-F])：\s*(.*)$")
ANS = re.compile(r"^正确答案：([A-F]+)\s*你的答案：([A-F]*)\s*$")
# 逐选项解析行：A. xxx / A、xxx / A．xxx
NOTE_LINE = re.compile(r"^([A-F])[.、．]\s*(.+)$")
# 「A、B、D选项均是……」这种一句话覆盖多个选项的行
MULTI_OPT = re.compile(r"^([A-F][、,，])+[A-F]")
# 漏了字母的解析行：'. 落后者：……'
ORPHAN_LINE = re.compile(r"^[.、．]\s*(.+)$")

# 选项解析里 ③ 的小标题
OTHERS_TITLE = "其他答案不正确解析："
SECTION_RE = re.compile(r"^([①②③④])")

# 被拍平的表格：正文行与空行交替出现。单元格必须短、且不以「：」结尾
# （后者用来把「其他类型路线图（指南第1.7节）：」这类小标题挡在表格外）
CELL_MAXLEN = 30
CELL_TAIL = ("：", ":")


class ConvertError(Exception):
    pass


# ---------------------------------------------------------------- 解析

def read_lines(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    return raw.replace("﻿", "").split("\n")


def split_questions(lines):
    """按 `N、 [单选] 题干` 切成题目块。"""
    questions, cur, mode = [], None, None
    for lineno, ln in enumerate(lines, 1):
        m = Q_START.match(ln)
        if m:
            if cur:
                questions.append(cur)
            cur = {"no": int(m.group(1)), "kind": m.group(2), "q": [m.group(3)],
                   "opts": [], "ans": None, "jiexi": [], "line": lineno}
            mode = "q"
            continue
        if cur is None:
            if ln.strip():
                raise ConvertError("第 %d 行不在任何题目内: %r" % (lineno, ln))
            continue
        mo = OPT.match(ln)
        if mo and mode in ("q", "opt"):
            cur["opts"].append([mo.group(1), mo.group(2)])
            mode = "opt"
            continue
        ma = ANS.match(ln)
        if ma:
            cur["ans"] = ma.group(1)
            mode = "ans"
            continue
        if ln.startswith("解析："):
            cur["jiexi"].append(ln[3:])
            mode = "jiexi"
            continue
        if mode == "q":
            cur["q"].append(ln)
        else:
            cur["jiexi"].append(ln)
    if cur:
        questions.append(cur)
    return questions


def join_wrapped(lines):
    """题干里被硬折行的句子接回去。

    只在上一条不以句末标点结尾、且下一条不以标点开头时拼接 —— 这两份题库里
    出现的折行都是这种（`……针对8~12` / `岁儿童的新产品。……`）。
    """
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if out and not re.search(r"[。！？；：.?!”』】]$", out) and not ln.startswith(("A：", "B：")):
            out += ln
        else:
            out += ("<br>" if out else "") + ln
    return out


def drop_flattened_tables(lines):
    """丢掉被拍平的表格行，返回 (保留下来的行, 丢掉了什么)。

    拍平后的表格长这样：每行一个单元格，单元格之间隔一个空行。
    """
    keep, dropped, i = [], [], 0
    while i < len(lines):
        ln = lines[i]
        if (ln.strip() and len(ln.strip()) <= CELL_MAXLEN
                and not ln.strip().endswith(CELL_TAIL) and i + 1 < len(lines)
                and not lines[i + 1].strip()):
            # 可能是一段表格的起点
            j, cells, blanks = i, 0, 0
            while j < len(lines):
                s = lines[j].strip()
                if not s:
                    blanks += 1
                    j += 1
                    continue
                if len(s) <= CELL_MAXLEN and not s.endswith(CELL_TAIL):
                    cells += 1
                    j += 1
                    continue
                break
            if cells >= 4 and blanks >= 3:
                dropped.append(lines[i:j])
                i = j
                continue
        keep.append(ln)
        i += 1
    return keep, dropped


def parse_explanation(jiexi, opt_letters, answer):
    """解析 → (note 段落, {字母: 逐选项解析}, 修补记录)

    note 段落按 ① ② ③补充 ④ 的顺序排。
    """
    sections, order, cur = {}, [], None
    for ln in jiexi:
        m = SECTION_RE.match(ln)
        if m:
            cur = m.group(1)
            if cur not in sections:
                sections[cur] = []
                order.append(cur)
            sections[cur].append(ln[1:])
        elif cur is not None:
            sections[cur].append(ln)

    fixes = []
    notes, extras = {}, []

    # ---- ③
    if "③" in sections:
        body = list(sections["③"])
        if body and body[0].strip() == OTHERS_TITLE:
            body = body[1:]
        body, dropped = drop_flattened_tables(body)
        if dropped:
            n = sum(1 for seg in dropped for t in seg if t.strip())
            fixes.append("③ 里丢掉拍平表格 %d 个单元格" % n)

        entries = []
        for s in body:
            s = s.strip()
            if not s:
                continue
            if MULTI_OPT.match(s):
                entries.append(("shared", s))
            else:
                m = NOTE_LINE.match(s)
                if m:
                    entries.append(("one", (m.group(1), m.group(2))))
                else:
                    m2 = ORPHAN_LINE.match(s)
                    entries.append(("orphan", m2.group(1)) if m2 else ("after", s))

        # 漏字母的行：题干恰好只缺一个应有字母时认领
        expected = [l for l in opt_letters if l != answer]
        missing = [l for l in expected if l not in
                   [v[0] for k, v in entries if k == "one"]]
        orphan_idx = [i for i, (k, _) in enumerate(entries) if k == "orphan"]
        if len(orphan_idx) == 1 and len(missing) == 1:
            i = orphan_idx[0]
            entries[i] = ("one", (missing[0], entries[i][1]))
            fixes.append("③ 补回漏掉的选项字母 %s" % missing[0])
        elif orphan_idx:
            fixes.append("③ 有 %d 行没选项字母、且缺 %d 个字母 —— 未修补"
                         % (len(orphan_idx), len(missing)))

        last_one = max([i for i, (k, _) in enumerate(entries) if k == "one"],
                       default=-1)
        for i, (k, v) in enumerate(entries):
            if k == "one":
                notes[v[0]] = v[1]
            elif k == "shared":
                extras.append(v)
            elif k == "orphan":
                extras.append(v)
            elif k == "after" and i > last_one:
                extras.append(v)

        # 有的题 ③ 是一整句总结（如「A、B、D选项均是……四个标准维度之一。」）
        # 拆不到单个选项，就当作 note 的补充段落

    # ---- 拼 note
    parts = []
    for key in ("①", "②"):
        if key in sections:
            body, _ = drop_flattened_tables(sections[key])
            txt = "<br>".join(t.strip() for t in body if t.strip())
            if txt:
                parts.append(txt)
    if extras:
        parts.append("<br>".join(extras))
    if "④" in sections:
        body, dropped = drop_flattened_tables(sections["④"])
        if dropped:
            n = sum(1 for seg in dropped for t in seg if t.strip())
            fixes.append("④ 里丢掉拍平表格 %d 个单元格" % n)
        txt = "<br>".join(t.strip() for t in body if t.strip())
        if txt:
            parts.append(txt)
    return parts, notes, fixes


# ---------------------------------------------------------------- 去重

def _norm(s):
    s = re.sub(r"\s+", "", s)
    for a, b in [("，", ","), ("。", "."), ("、", ","), ("？", "?"), ("：", ":"),
                 ("（", "("), ("）", ")"), ("“", '"'), ("”", '"'), ("；", ";")]:
        s = s.replace(a, b)
    return s


def dedupe(questions):
    """同一道题出现多次时保留首次出现的题号。返回 (保留的题目, 丢弃记录)。"""
    dropped = []

    # 第一轮：题干+选项+答案逐字相同
    seen = {}
    keep = []
    for q in questions:
        key = (_norm("".join(q["q"])),
               tuple(_norm(t) for _, t in q["opts"]),
               q["ans"])
        if key in seen:
            dropped.append((q["no"], seen[key], "逐字相同"))
            continue
        seen[key] = q["no"]
        keep.append(q)

    # 第二轮：题干只差个别字词、选项与答案逐字相同
    out = []
    for q in keep:
        qn = _norm("".join(q["q"]))
        qo = tuple(_norm(t) for _, t in q["opts"])
        dup_of = None
        for p in out:
            if p["ans"] != q["ans"]:
                continue
            if tuple(_norm(t) for _, t in p["opts"]) != qo:
                continue
            if qn == _norm("".join(p["q"])):
                continue
            r = difflib.SequenceMatcher(None, qn, _norm("".join(p["q"]))).ratio()
            if r >= 0.85:
                dup_of = p["no"]
                break
        if dup_of is not None:
            dropped.append((q["no"], dup_of, "近义重复 ratio>=0.85"))
            continue
        out.append(q)
    return out, dropped


# ---------------------------------------------------------------- 输出

def html(t):
    return t.replace("\t", " ").replace("<br>", "\n").replace("\n", "<br>")


def build_rows(questions, chapter):
    rows = []
    for q in questions:
        letters = [l for l, _ in q["opts"]]
        parts, notes, fixes = parse_explanation(q["jiexi"], letters, q["ans"])
        if not q["ans"]:
            raise ConvertError("第 %d 题没有正确答案" % q["no"])
        bad = [l for l in q["ans"] if l not in letters]
        if bad:
            raise ConvertError("第 %d 题答案 %s 不在选项 %s 里"
                               % (q["no"], q["ans"], "".join(letters)))
        if len(letters) != len(set(letters)):
            raise ConvertError("第 %d 题选项字母重复" % q["no"])
        note = "<br><br>".join(parts)
        row = [
            "npdp-%s-%03d" % (chapter, q["no"]),
            join_wrapped(q["q"]),
        ]
        for l in "ABCDEF":
            row.append(dict(q["opts"]).get(l, ""))
        row.append(q["ans"])
        row.append(note)
        for l in "ABCDEF":
            row.append(notes.get(l, ""))
        row.append(CHAPTER if chapter == "1" else "第%s章" % chapter)
        rows.append((q["no"], row, fixes, letters, notes))
    return rows


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else re.sub(r"\.md$", ".tsv", src)
    m = re.search(r"chapter-(\d+)", src)
    if not m:
        raise ConvertError("从文件名里看不出章节号: %s" % src)
    chapter = m.group(1)

    questions = split_questions(read_lines(src))
    print("读入 %d 题（题号 %d..%d）"
          % (len(questions), questions[0]["no"], questions[-1]["no"]))

    kept, dropped = dedupe(questions)
    print("去掉 %d 题重复，剩余 %d 题" % (len(dropped), len(kept)))
    for n, of, why in dropped:
        print("   丢 %d（与 %d %s）" % (n, of, why))

    rows = build_rows(kept, chapter)
    all_fixes = [(no, f) for no, _, f, _, _ in rows if f]
    print("修补 %d 题：" % len(all_fixes))
    for no, f in all_fixes:
        print("   %d: %s" % (no, "; ".join(f)))

    header = ["id", "question"] + ["option" + l for l in "ABCDEF"] + ["answer", "note"] \
        + ["note" + l for l in "ABCDEF"] + ["source"]
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for _, row, _, _, _ in rows:
            assert len(row) == len(header), len(row)
            f.write("\t".join(c.replace("\t", " ").replace("\n", "<br>")
                              for c in row) + "\n")
    print("写出 %s（%d 列 × %d 行，不含表头）" % (dst, len(header), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
