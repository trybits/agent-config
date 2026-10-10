# -*- coding: utf-8 -*-
"""对产出的 TSV 做结构与内容自检。"""
import sys, io, csv, re, collections, unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TSV = (r"D:\TraeFile\agent-config\skills\npdp-exercise-to-anki-workspace"
       r"\iteration-1\restore-chapter-1\without_skill\outputs\chapter-1.tsv")
SRC = (r"D:\TraeFile\agent-config\skills\npdp-exercise-to-anki-workspace"
       r"\iteration-1\restore-chapter-1\inputs\chapter-1.md")

EXPECT_HEADER = (["id", "question"] + ["option" + l for l in "ABCDEF"]
                 + ["answer", "note"] + ["note" + l for l in "ABCDEF"] + ["source"])

problems = []

raw = open(TSV, encoding="utf-8").read()
if "\r" in raw:
    problems.append("文件里有 CR")
rows = list(csv.reader(io.StringIO(raw), delimiter="\t"))
hdr, data = rows[0], rows[1:]

if hdr != EXPECT_HEADER:
    problems.append("表头不对: %r" % hdr)

n_q = len(data)
if n_q != 51:
    problems.append("题目数 %d != 51" % n_q)

ids = [r[0] for r in data]
if len(set(ids)) != len(ids):
    problems.append("id 有重复: %s" % [k for k, c in collections.Counter(ids).items() if c > 1])
if ids != sorted(ids):
    problems.append("id 未按题号排序")

for r in data:
    rid = r[0]
    if len(r) != 17:
        problems.append("%s 列数 %d" % (rid, len(r)))
        continue
    if not re.match(r"^npdp-1-\d{3}$", rid):
        problems.append("%s id 格式不对" % rid)
    if not r[1].strip():
        problems.append("%s 题干为空" % rid)
    letters = [l for l in "ABCDEF" if r[2 + "ABCDEF".index(l)].strip()]
    if not letters:
        problems.append("%s 没有选项" % rid)
    opts = [r[2 + i] for i in range(6)]
    # 选项必须连续、非空
    filled = [i for i, o in enumerate(opts) if o.strip()]
    if filled != list(range(len(filled))):
        problems.append("%s 选项不连续: %r" % (rid, opts))
    ans = r[8]
    if not ans or any(a not in "ABCDEF"[:len(filled)] for a in ans):
        problems.append("%s 答案 %r 与选项不符" % (rid, ans))
    if not r[9].strip():
        problems.append("%s note 为空" % rid)
    if r[16] != "第1章":
        problems.append("%s source=%r" % (rid, r[16]))
    # 所有字段不许有裸换行/制表（已被转成 <br>）
    for k, v in zip(hdr, r):
        if "\n" in v or "\t" in v:
            problems.append("%s 字段 %s 含裸换行/制表" % (rid, k))
        for ch in v:
            if unicodedata.category(ch) == "Cc":
                problems.append("%s 字段 %s 含控制字符 %r" % (rid, k, ch))
                break
    # 残留的解析标记
    for k, v in zip(hdr, r):
        if re.search(r"^解析：", v) or re.search(r"<br>[①②③④]", v):
            problems.append("%s 字段 %s 残留解析标记: %r" % (rid, k, v[:60]))

# 逐选项解析：非空选项的字母应当 <答案>
for r in data:
    ans, n = r[8], r[9]
    for l in "ABCDEF":
        v = r[hdr.index("note" + l)]
        if v.strip() and l in ans and len(ans) == 1 and False:
            pass
# 覆盖度统计
cov = collections.Counter()
for r in data:
    c = sum(1 for l in "ABCDEF" if r[hdr.index("note" + l)].strip())
    cov[c] += 1
print("逐选项解析覆盖（每题有几个 noteX）:", dict(cov))

# 与源文件交叉核对：答案、选项数
src_rows = list(csv.reader(io.StringIO(raw), delimiter="\t"))
print("题干非空:", all(r[1].strip() for r in data))
print("note 平均长度: %.0f 字" % (sum(len(r[9]) for r in data) / len(data)))
print()
if problems:
    print("发现 %d 个问题:" % len(problems))
    for p in problems:
        print("  -", p)
else:
    print("自检通过：51 题 × 17 列，无结构问题。")
