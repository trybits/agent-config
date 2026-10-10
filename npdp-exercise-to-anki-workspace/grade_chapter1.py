#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eval-0 的自动判分：把产出的 TSV 和仓库基准逐列比对。

设计要点：不要求逐字全等。修复文件里那 7 道题的 note 文本是人工撰写的，
措辞必然不同，拿它当标准答案会误判。所以拆成两层：

  * 硬断言（必须逐字一致）：id / question / optionA–F / answer / source
    —— 这些列完全来自题库原文，不该有任何出入
  * 软断言：未受缺陷影响的题，note / noteA–F 也应逐字一致

用法：
    python grade_chapter1.py <候选.tsv> <基准.tsv>
输出 JSON：{"checks": [{"text":..., "passed":..., "evidence":...}, ...]}
"""

import json
import pathlib
import sys

# 解析原文有毛病、修复文本必然因人而异的那些题（chapter-1 的场景）
REPAIRED = {10, 34, 59, 60, 62, 63, 65}

LETTERS = "ABCDEF"
ID_COLS = ["id", "question", "answer", "source"] + \
          ["option" + L for L in LETTERS]
TEXT_COLS = ["note"] + ["note" + L for L in LETTERS]

# 这些片段出现在 note 里是对的（人工修复把它们挪过去了），
# 但绝不能出现在某个选项的解析里 —— 那正是静默错位的形态。
COL = {name: 9 + i for i, name in enumerate(["note"] + ["note" + L for L in LETTERS])}
LEAK_CHECKS = [
    ("B、D选项均是", ["noteA", "noteB", "noteD"],
     "Q10/Q34 合并成一行的内容被错当成某个选项的解析"),
    (". 落后者：", ["noteA"],
     "Q62 漏了字母的行被原样塞进 noteA"),
    ("三者都是衰退阶段可能采取的策略", ["noteA", "noteB", "noteC", "noteD"],
     "Q63 ③ 末尾的游离段落被塞进某个选项的解析"),
]


def load(path):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    rows = [l.split("\t") for l in text.rstrip("\n").split("\n")]
    return rows


def qno(row_id):
    """npdp-1-062 → 62"""
    try:
        return int(row_id.rsplit("-", 1)[1])
    except (ValueError, IndexError):
        return None


def main(cand_path, base_path):
    checks = []

    def check(text, passed, evidence=""):
        checks.append({"text": text, "passed": bool(passed),
                       "evidence": str(evidence)[:400]})

    try:
        cand = load(cand_path)
    except FileNotFoundError:
        check("产出 TSV 存在", False, f"找不到 {cand_path}")
        print(json.dumps({"checks": checks}, ensure_ascii=False, indent=2))
        return

    base = load(base_path)
    check("产出 TSV 存在", True, cand_path)

    check("TSV 恰好 51 行（去重后题数正确）", len(cand) == 51,
          f"实际 {len(cand)} 行")

    bad_cols = [(i + 1, len(r)) for i, r in enumerate(cand) if len(r) != 17]
    check("每行恰好 17 列", not bad_cols, f"行列数异常：{bad_cols[:5]}")

    # 行数不符时不要短路 —— 后面的逐列比对依然有信息量，
    # 在 id 交集上继续比，差的那些行由上面「id 集合」那条断言负责报。
    extra_rows = [r[0] for r in cand if r[0] not in {x[0] for x in base}]
    if extra_rows:
        check("产出里没有多余的行（如表头行）", False,
              f"多出 {len(extra_rows)} 行：{extra_rows[:4]}")
    else:
        check("产出里没有多余的行（如表头行）", True)

    # 按 id 建索引，在交集上比
    bi = {r[0]: r for r in base}
    ci = {r[0]: r for r in cand}

    check("id 集合与基准一致", set(bi) == set(ci),
          f"多出 {sorted(set(ci) - set(bi))[:5]}，缺少 {sorted(set(bi) - set(ci))[:5]}")

    still_dup = [i for i in ci if qno(i) in {31, 46, 52}]
    check("重复题 31/46/52 已去掉", not still_dup, f"仍存在：{still_dup}")

    # 硬断言：原文列逐字一致。
    # 列顺序由 FIELD_ORDER 决定，两边一致，直接按下标比：
    # 0=id 1=question 2-7=optionA-F 8=answer ... 16=source
    diff = []
    for rid in sorted(set(bi) & set(ci)):
        rb, rc = bi[rid], ci[rid]
        for idx in range(9):  # 0..8：id question optionA-F answer source
            if rb[idx] != rc[idx]:
                diff.append(f"{rid} 第{idx+1}列 {rb[idx][:30]!r} != {rc[idx][:30]!r}")
    check("id/题干/选项/答案/来源 九列与基准逐字一致", not diff,
          "\n".join(diff[:6]))

    # 软断言：未受影响题目的解析逐字一致
    note_diff = []
    for rid in sorted(set(bi) & set(ci)):
        if qno(rid) in REPAIRED:
            continue
        rb, rc = bi[rid], ci[rid]
        for idx in range(9, 17):  # note, noteA..F
            if rb[idx] != rc[idx]:
                note_diff.append(f"{rid} 第{idx+1}列")
    check("未受缺陷影响题的 note/noteX 与基准逐字一致", not note_diff,
          "\n".join(note_diff[:6]))

    # 坏文本不该错位进某个选项的解析里
    leftovers = []
    for rid, rc in ci.items():
        for snip, cols, why in LEAK_CHECKS:
            for col in cols:
                if snip in rc[COL[col]]:
                    leftovers.append(f"{rid}.{col}: {why}")
    check("坏解析片段没有错位进某个选项的解析", not leftovers,
          "\n".join(leftovers[:6]))

    # 受影响的题应当有实质解析，而不是被清空
    emptied = []
    for rid, rc in ci.items():
        if qno(rid) in REPAIRED and not rc[9].strip():
            emptied.append(rid)
    check("受影响题的 note 非空（修复生效而非清空）", not emptied,
          "\n".join(emptied[:6]))

    print(json.dumps({"checks": checks}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("用法：python grade_chapter1.py <候选.tsv> <基准.tsv>")
    main(sys.argv[1], sys.argv[2])
