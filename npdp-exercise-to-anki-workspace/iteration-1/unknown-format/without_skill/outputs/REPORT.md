# mock-exam-1.md → Anki 导入：调研与处理报告

## 结论速览

| 问题 | 结论 |
|---|---|
| 这份文档是什么格式 | 一份**模拟题**（6 题），写法与仓库里已有的章节题库**完全不同** |
| 现有管线能直接处理吗 | **不能**。不报错，但会静默产出 0 题的空 TSV —— 比报错更危险 |
| 做了什么 | 给 `scripts/npdp_to_anki.py` 加了第二种格式的解析分支 + 格式自动识别；补了测试 |
| 产物 | `mock-exam-1.tsv`，6 行 × 17 列，可直接导入 |

---

## 一、这份文档的实际格式

```markdown
# NPDP 模拟题 第一套

共 6 题，限时 10 分钟。

---

**1.** 产品创新章程（Product Innovation Charter）中，"边界" 部分主要用于说明什么？

A. 产品的目标市场规模与增长预期
B. 产品不做哪些事、不进入哪些市场
C. 项目团队的组成与汇报关系
D. 产品的定价区间

答案：B

解析：产品创新章程由背景、焦点、目标、边界四部分组成。边界部分明确划定范围之外的内容，用于防止范围蔓延。

---
```

与仓库既有的 `docs/npdp/exercise/chapter-1.md`（管线原本只认这种）逐项对比：

| 位置 | 章节题库（旧） | 本次的模拟题（新） |
|---|---|---|
| 题号行 | `1、 [单选] 题干` | `**1.** 题干` |
| 题号行是否带题型 | 带 `[单选]` / `[多选]` 标签 | **不带**，多选靠题干里的 `（多选）` |
| 选项 | ` A：选项一`（前导空格 + 全角冒号） | `A. 选项一`（顶格 + 半角句点） |
| 答案行 | `正确答案：B 你的答案：D`（带用户作答） | `答案：B`（无用户作答） |
| 解析 | `解析：①考点提炼…②正确答案解析…③其他答案不正确解析：` + 逐选项 `A. …` + `④考点延展…` | `解析：` + **一整段散文**，无 ①②③④ 分节，无逐选项解析 |
| 题间分隔 | 无 | `---` |
| 文档头 | 无 | `# NPDP 模拟题 第一套` + 「共 6 题」前言 |
| 文件名 | `chapter-N.md` | `mock-exam-1.md` |

6 题内容本身没问题：选项齐整（每题 A–D，连续）、答案字母都在选项范围内、
`（多选）` 标记与答案长度一致（Q2/Q5 是 AC，其余单选）、解析都完整。
**没有发现题目内容或答案键的错误。**

## 二、现有管线为什么处理不了

`scripts/npdp_to_anki.py` 的解析全部建立在旧格式的正则上：

```python
_Q_RE   = re.compile(r"^(\d+)、\s*\[(单选|多选)\]\s*(.*)$")
_OPT_RE = re.compile(r"^ ([A-F])：\s*(.*)$")
_ANS_RE = re.compile(r"^正确答案：([A-F]+)\s+你的答案：([A-F]+)\s*$")
```

对这份文档逐条都匹配不上。实测结果：

```
$ python scripts/npdp_to_anki.py mock-exam-1.md     # 改名前
题库格式有问题，已停手：文件名里找不到章节号          # EXIT=1

$ python -c "npdp_to_anki.parse_questions(mock_exam_text)"
parsed questions: 0                                  # 题号行一行都没匹配上
```

即：**如果文件名叫 `chapter-9.md`，脚本会开心地写出一份 0 行的 TSV 并打印「0 题」**
（`parse_questions` 在没有任何题号行时返回空列表，不报错）。这是本次顺带修掉的问题。

`split_note()` 也会炸——它硬性要求解析里有 ①②③④ 四个标记，而模拟题的解析是一整段散文。

## 三、改了什么

在 `scripts/npdp_to_anki.py` 里**新增**第二种格式的分支，旧路径一行没动：

1. **新解析器** `_parse_mock_block()` —— 认 `**N.**` 题号行、`A.` 选项、`答案：X`、
   `解析：` 后到 `---` 为止的散文。
2. **格式自动识别** `detect_format()` —— 按题号行的写法二选一。
   **认不出就 `ParseError`，不再返回 0 道题**（这是对旧版静默行为的修正）。
3. **新行构造器** `_build_mock_row()` —— 整段解析进 `note`，`noteA…noteF` 全空。
   `build_row()` 按 `Question.fmt` 分派，旧的 `_build_chapter_row()` 原样保留。
4. **来源识别** `source_of()` —— 取名中的 `chapter-N` 当章节号；否则用文件名 stem
   当 id 前缀、文档一级标题当 `source`。
5. **模拟题的完整性自检** `_check_mock()` —— 缺题干/选项/答案/解析、选项字母不连续、
   答案字母不在选项里、`（多选）` 标记与答案长度对不上，全部 `ParseError`。
   另加：解析区里出现认不出的行（题干换行、粘进表格）也报错，不静默吞掉。
6. **一处防撞车** —— 模拟题内容存成 `chapter-N.md` 会拿到 `npdp-N-*` 的 id，
   和真正的第 N 章撞车（重导入会覆盖已有卡片）。现在直接拦下并提示改名。

未改动：`templates/mcq/` 下的 Anki 模板、样式、JS 全部没碰；`chapter-1.tsv` 一字未变。

## 四、字段映射（模拟题）

| 字段 | 值 |
|---|---|
| `id` | `npdp-mock-exam-1-001` … `-006`（文件名 stem 当命名空间） |
| `question` | 题干，`（多选）` 标记已剥掉 |
| `optionA`–`optionD` | 选项原文 |
| `optionE` / `optionF` | 空（模板会自动隐藏） |
| `answer` | `B` / `AC` 等 |
| `note` | 「解析：」之后的那段散文 |
| `noteA`–`noteF` | **全空**——原文没有逐选项解析 |
| `source` | `NPDP 模拟题 第一套`（文档一级标题） |

## 五、两个需要你知道的决定

**1. 剥掉了题干里的「（多选）」。**
笔记类型由 `answer` 的长度自己判多选并显示「多选题」标签
（`templates/mcq/README.md`），留着会在卡面上重复显示一遍。
这也与旧管线一致——旧格式的 `[多选]` 标签同样没进题干。
为防剥掉时丢掉信息，脚本会核对「标记存在」与「`answer` 长度 > 1」是否一致，
不一致就报错（多半是答案键漏抄了字母）。

**2. 没做 `mock-exam-1.fixes.md`。**
这份文档的解析是散文，没有旧格式那种 ①②③④ 分节，也就没有「③ 拆出来的选项字母
和错误答案对不上」这类坏格式。6 题全部一次解析通过，不需要修复文件。
脚本仍支持给模拟题追加 `note_extra`，将来真需要时可用。

## 六、验证

```
$ python -m unittest discover -s scripts/tests -t scripts/tests
Ran 102 tests ... OK          # 原有 55 个 + 新增 47 个

$ node --test templates/mcq/tests/core.test.js
pass 20 / fail 0

$ python scripts/npdp_to_anki.py docs/npdp/mock/mock-exam-1.md
docs\npdp\mock\mock-exam-1.md → docs\npdp\mock\mock-exam-1.tsv：6 题
```

回归保证：改动前后重跑 `chapter-1.md`，产物 **SHA-256 完全一致**
（`dfc249498193b7f6…`），且等于仓库里已提交的 `chapter-1.tsv`。
新测试 `test_mock_exam.py::TestChapterFormatUnaffected` 把这个不变量钉住了。

产物体检：6 行、每行 17 列、无字段内含裸换行或制表符。

## 七、遗留的不确定项

1. **行尾是 CRLF。** `write_text` 在 Windows 上把 `\n` 写成 `\r\n`，所以产物是 CRLF。
   这不是本次引入的——已提交的 `chapter-1.tsv` 同样是 CRLF，Anki 导入正常
   （实测确认 CR 只出现在行尾，没有任何字段内部含 CR/LF）。为不制造无谓的
   diff，**没有**改成 LF。
2. **改文件名会导致重复导入。** 模拟题的 `id` 前缀取自文件名
   （`mock-exam-1` → `npdp-mock-exam-1-001`），改名后重导入会多出一份卡片，
   而不是按 `id` 更新。要改文件名的话，建议同时改 Anki 里的旧卡片或先删掉。
3. **`（多选）` 一致性检查是硬失败。** 若将来某份模拟题忘了写 `（多选）`
   却给了多字母答案，脚本会整体停下要求改原文，而不是照 `answer` 继续。
   这是刻意的（沿用仓库「不猜」的一贯做法），但确实会挡住导入。
4. **只验了这一份。** 解析器按这份文档的写法写的。若你手上其余几套模拟题的
   版式有出入（比如题号写成 `**1．**` 全角点、选项没有句点、解析分多段带小标题），
   需要再看一份才能确认。
5. **没有提交 git。** 改动都在工作区里（`scripts/npdp_to_anki.py`、
   `scripts/tests/test_mock_exam.py`、`scripts/README.md`，新增
   `docs/npdp/mock/mock-exam-1.md` 与 `.tsv`），等你看过再决定要不要提交。

## 八、跑一遍

```bash
cd D:\repositories\repos-personal\anki
python scripts/npdp_to_anki.py docs/npdp/mock/mock-exam-1.md
# → docs/npdp/mock/mock-exam-1.tsv：6 题
```

导入 Anki：笔记类型选「NPDP 选择题」→ 分隔符 Tab → **勾上「允许 HTML 字段」**
→ 重复处理选「与首字段相同的笔记」。

题库源文件已放进仓库 `docs/npdp/mock/mock-exam-1.md`，这样管线可复跑、测试有真实
夹具（沿用仓库既有的「测试直接跑真实题库」做法）。

## 附：本目录里的文件

| 文件 | 说明 |
|---|---|
| `mock-exam-1.tsv` | **产物**，6 行 × 17 列，直接导入 Anki |
| `mock-exam-1.md` | 源文档副本（仓库内位置：`docs/npdp/mock/mock-exam-1.md`） |
| `npdp_to_anki.py` | 改过的转换脚本（仓库内位置：`scripts/npdp_to_anki.py`） |
| `test_mock_exam.py` | 新增的测试（仓库内位置：`scripts/tests/test_mock_exam.py`） |
| `scripts-README.md` | 更新过的脚本文档（仓库内位置：`scripts/README.md`） |
