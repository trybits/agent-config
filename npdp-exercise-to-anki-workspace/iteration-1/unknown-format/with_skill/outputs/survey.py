#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""题库文档体检：转换之前先摸清它实际长什么样。

题库文档表面上看起来极其规整，坏的地方藏在很具体的位置，而且坏掉之后
不报错、卡片还能正常渲染，只是你会背下一条张冠李戴的解析。所以动手前
先跑这个，把「实际有多少题、哪些题解析拆不出来、哪些题是重复的」查清楚，
而不是凭一眼的印象开工。

用法：
    python survey.py <题库.md> [--threshold 0.75]

输出四个部分：文档形状 / 需要修复的题 / 重复题 / 未知格式时的线索。

体检的标准必须和转换器是同一套，否则会一直喊狼来了：解析分清 ①②③④ 的
章节题库才查「③ 拆不拆得出来、④ 有没有表格碎片」；模拟题的解析是整段散文，
本来就没有 ③④，不套这条标准。
"""

import argparse
import difflib
import pathlib
import re
import sys
from collections import Counter


def find_repo(start):
    """向上找带 scripts/npdp_to_anki.py 的目录，那个才是仓库根。"""
    here = pathlib.Path(start).resolve()
    for cand in [here, *here.parents]:
        if (cand / "scripts" / "npdp_to_anki.py").exists():
            return cand
    return None


def load_converters(md_path):
    """把仓库里的转换模块 import 进来，保证体检标准和转换标准是同一套。"""
    repo = find_repo(md_path if pathlib.Path(md_path).is_dir()
                     else pathlib.Path(md_path).parent)
    if repo is None:
        repo = find_repo(pathlib.Path.cwd())
    if repo is None:
        sys.exit("找不到 scripts/npdp_to_anki.py —— 请在仓库内运行，"
                 "或用仓库内的路径指向题库文件。")
    sys.path.insert(0, str(repo / "scripts"))
    import npdp_to_anki as m  # noqa: E402
    return m, repo


def hr(title):
    print()
    print("=" * 68)
    print(title)
    print("=" * 68)


def fmt_of(q):
    """题目的格式名。老版转换模块没有 fmt，按章节题库算。"""
    return getattr(q, "fmt", "chapter")


def report_shape(m, text):
    hr("文档形状")
    try:
        questions = m.parse_questions(text)
    except m.ParseError as e:
        # 转换器在解析阶段就停手了（认不出格式、或模拟题缺件/自相矛盾）。
        # 这本身就是要报给用户的结果，别让它变成一个 traceback。
        print(f"解析阶段就停手了：{e}")
        print()
        print("这不是脚本坏了，是它认不出这份文档的格式，或者原文缺件。")
        print("先看下面「未知格式的线索」，把格式摸清楚再动手。")
        return []

    if not questions:
        print("按现有格式解析出 0 道题。这份文档的结构和 chapter-1 不一样，")
        print("先看下面「未知格式的线索」，把格式摸清楚再改解析器。")
        return questions

    fmts = Counter(fmt_of(q) for q in questions)
    print(f"格式：{dict(fmts)}   （chapter = 章节题库，mock = 模拟题）")
    print(f"题数：{len(questions)}")
    nos = [q.no for q in questions]
    print(f"题号：{min(nos)}–{max(nos)}，连续：{nos == sorted(nos)}，"
          f"唯一：{len(set(nos)) == len(nos)}")
    print(f"题型：{dict(Counter(q.kind for q in questions))}")
    print(f"选项数：{dict(Counter(len(q.options) for q in questions))}")
    print(f"答案长度：{dict(Counter(len(q.answer) for q in questions))}"
          "   （>1 即多选）")
    no_answer = [q.no for q in questions if not q.answer]
    if no_answer:
        print(f"没有答案的题：{no_answer}")
    return questions


def report_breaks(m, questions, fixes):
    """列出「套用修复之后」仍然有问题的题。

    判定方式和 build_row 完全一致 —— 已经在修复文件里处理过的题不该再报，
    否则这份体检会一直喊狼来了。
    """
    hr("解析拆不出来、需要写修复条目的题")
    bad = []
    mock = []
    for q in questions:
        fix = fixes.get(q.no, {})
        # 模拟题的解析是整段散文，压根没有 ①②③④，转换时走 _build_mock_row
        # 那条路（见 npdp_to_anki.build_row）。拿四段式的尺子去量它，只会
        # 把每一题都报成坏的 —— 体检的标准必须和转换的标准是同一套。
        # 模拟题原文缺件在解析阶段就已经报错了，这里没什么可查的。
        if fmt_of(q) == "mock":
            mock.append(q.no)
            continue
        try:
            sec = m.split_note(q.note_raw)
        except m.ParseError as e:
            bad.append((q.no, f"解析分段有毛病：{e}"))
            continue

        others = fix.get("others", sec["others"])
        ext = fix.get("extension", sec["extension"])
        wrong = sorted(set(q.options) - set(q.answer))
        try:
            if others.strip():
                m.parse_others(others, wrong, no=q.no)
        except m.ParseError as e:
            bad.append((q.no, str(e)))
            continue
        if m.extension_needs_fix(ext):
            bad.append((q.no, "④ 里有拍平的表格碎片（修复文件里还没有 extension 条目）"))

    if not bad:
        if mock and not [q for q in questions if fmt_of(q) != "mock"]:
            print(f"没有。这 {len(mock)} 题都是模拟题格式：解析是一整段散文，"
                  "没有 ③ 逐选项解析，也没有 ④，转换时原样进 note 字段，"
                  "不需要修复条目。")
        elif mock:
            print("没有。章节题库那部分每题的 ③ 都能拆成逐选项解析、④ 也没有"
                  "表格碎片；模拟题那部分本来就没有 ③④，不需要修复条目。")
        else:
            print("没有。所有题的 ③ 都能拆成逐选项解析，④ 也没有表格碎片。")
    else:
        print(f"共 {len(bad)} 题：\n")
        for no, why in bad:
            print(f"  Q{no}: {why}")
        print("\n这些题各需要在 <题库>.fixes.md 里加一条修复。")
        print("不要为了让它们过而放宽解析器的校验 —— 那正是把错解析")
        print("悄悄带进卡片的路径。")


def report_dupes(m, questions, manual, threshold):
    hr("重复题")
    _kept_auto, auto_dropped = m.dedupe(questions)

    print(f"逐字重复（自动去掉）：{len(auto_dropped)} 组")
    for d, k in auto_dropped:
        print(f"  Q{d} = Q{k}")

    print()
    if manual:
        print(f"手工去重清单（修复文件的「## 手工去重」段）：{len(manual)} 条")
        for d, k in sorted(manual.items()):
            print(f"  Q{d} = Q{k}")
    else:
        print("手工去重清单：空")

    # 近似重复只看还没被处理的 —— 已进手工清单的不必再报
    handled = set(manual)
    remaining = [q for q in _kept_auto if q.no not in handled]
    pairs = []
    for i, a in enumerate(remaining):
        for b in remaining[i + 1:]:
            r = difflib.SequenceMatcher(None, a.stem, b.stem).ratio()
            if r >= threshold:
                pairs.append((r, a, b))
    pairs.sort(reverse=True)

    print()
    if not pairs:
        print(f"近似重复（相似度 ≥ {threshold}，且还没处理的）：无")
    else:
        print(f"近似重复（相似度 ≥ {threshold}，且还没处理的）：{len(pairs)} 组")
        print("自动比对是逐字比较，抓不到换个说法的同一道题，"
              "这些要写进修复文件的「## 手工去重」段。\n")
        for r, a, b in pairs:
            same = "选项相同" if a.options == b.options else "选项不同"
            ans = "答案相同" if a.answer == b.answer else "答案不同"
            print(f"  {r:.2f}  Q{a.no} / Q{b.no}  （{same}，{ans}）")
            print(f"        Q{a.no}: {a.stem}")
            print(f"        Q{b.no}: {b.stem}")

    print()
    kept, dropped = m.dedupe(questions, manual)
    print(f"去重后题数：{len(kept)}（原 {len(questions)}，"
          f"去掉 {len(dropped)} 题）")


def report_unknown_format(text):
    """解析不出题时，给出足够线索让 Claude 判断真实格式。"""
    hr("未知格式的线索")
    lines = text.split("\n")
    nonempty = [l for l in lines if l.strip()]
    print(f"总行数 {len(lines)}，非空行 {len(nonempty)}\n")

    print("非空行的开头字符分布（前 20）：")
    heads = Counter()
    for l in nonempty:
        s = l.strip()
        m = re.match(r"^([^\s]{1,4})", s)
        if m:
            heads[m.group(1)] += 1
    for head, n in heads.most_common(20):
        print(f"  {n:5d}  {head!r}")

    print("\n前 40 个非空行：")
    for l in nonempty[:40]:
        print("  |" + l[:90])


def main(argv=None):
    ap = argparse.ArgumentParser(description="题库文档体检")
    ap.add_argument("md", help="题库 markdown 路径")
    ap.add_argument("--threshold", type=float, default=0.75,
                    help="近似重复判定阈值，默认 0.75")
    args = ap.parse_args(argv)

    md_path = pathlib.Path(args.md)
    if not md_path.exists():
        sys.exit(f"没有这个文件：{md_path}")

    m, repo = load_converters(md_path)
    text = md_path.read_text(encoding="utf-8")

    fixes_path = md_path.with_name(md_path.stem + ".fixes.md")
    has_fixes = fixes_path.exists()
    fixes = m.load_fixes(fixes_path) if has_fixes else {}
    manual = m.load_manual_dupes(fixes_path) if has_fixes else {}

    print(f"仓库根：{repo}")
    print(f"题库文件：{md_path}")
    print(f"修复文件：{fixes_path if has_fixes else '（还没有）'}")

    questions = report_shape(m, text)
    if not questions:
        report_unknown_format(text)
        return 1

    report_breaks(m, questions, fixes)
    report_dupes(m, questions, manual, args.threshold)

    hr("下一步")
    print("1. 上面列出的坏题，逐条在修复文件里写替代文本")
    print("2. 近似重复的，写进修复文件的「## 手工去重」段")
    print(f"3. python scripts/npdp_to_anki.py {md_path}")
    print("4. 再跑一次本体检，确认「需要修复的题」清空了")
    return 0


if __name__ == "__main__":
    sys.exit(main())
