# -*- coding: utf-8 -*-
"""模拟题格式（docs/npdp/mock/*.md）的单元测试。

运行： python -m unittest discover -s scripts/tests -t scripts/tests

和 chapter-1 的测试一样，这里直接跑真实的题库文件，所以它同时是一份
「格式体检」——模拟题原文改了样子，测试会红。
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import npdp_to_anki as m  # noqa: E402

MOCK1 = ROOT / "docs" / "npdp" / "mock" / "mock-exam-1.md"
CHAPTER1 = ROOT / "docs" / "npdp" / "exercise" / "chapter-1.md"


class TestDetectFormat(unittest.TestCase):
    """按题号行的写法认格式，认不出要报错而不是给零道题。"""

    def test_章节题库认成chapter(self):
        self.assertEqual(m.detect_format(CHAPTER1.read_text(encoding="utf-8")),
                         "chapter")

    def test_模拟题认成mock(self):
        self.assertEqual(m.detect_format(MOCK1.read_text(encoding="utf-8")),
                         "mock")

    def test_认不出时抛错(self):
        # 旧行为是静默返回 0 道题，产出一个空 TSV —— 那是无声的错数据
        with self.assertRaises(m.ParseError):
            m.detect_format("# 标题\n\n一段没有任何题号行的正文。\n")

    def test_空文件抛错(self):
        with self.assertRaises(m.ParseError):
            m.detect_format("")


class TestParseMockQuestions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = MOCK1.read_text(encoding="utf-8")
        cls.questions = m.parse_questions(cls.text)

    def test_切出全部6题(self):
        self.assertEqual(len(self.questions), 6)

    def test_题号连续且唯一(self):
        self.assertEqual([q.no for q in self.questions], list(range(1, 7)))

    def test_格式标记为mock(self):
        for q in self.questions:
            self.assertEqual(q.fmt, "mock", f"Q{q.no}")

    def test_题干选项答案正确(self):
        q = self.questions[0]
        self.assertEqual(
            q.stem, '产品创新章程（Product Innovation Charter）中，"边界" 部分主要用于说明什么？')
        self.assertEqual(q.options["A"], "产品的目标市场规模与增长预期")
        self.assertEqual(q.options["B"], "产品不做哪些事、不进入哪些市场")
        self.assertEqual(q.options["C"], "项目团队的组成与汇报关系")
        self.assertEqual(q.options["D"], "产品的定价区间")
        self.assertEqual(q.answer, "B")

    def test_每题四选项(self):
        for q in self.questions:
            self.assertEqual(sorted(q.options), ["A", "B", "C", "D"], f"Q{q.no}")

    def test_多选标记被剥掉且不影响题干其余部分(self):
        # 笔记类型由 answer 长度自己判多选，题干里留着「（多选）」是重复显示
        q2 = self.questions[1]
        self.assertNotIn("多选", q2.stem)
        self.assertEqual(q2.stem, "关于门径管理（Stage-Gate），以下说法正确的有哪些？")
        for q in self.questions:
            self.assertNotIn("（多选）", q.stem, f"Q{q.no}")

    def test_多选题的kind与答案(self):
        kinds = {q.no: q.kind for q in self.questions}
        self.assertEqual(kinds, {1: "单选", 2: "多选", 3: "单选",
                                 4: "单选", 5: "多选", 6: "单选"})
        answers = {q.no: q.answer for q in self.questions}
        self.assertEqual(answers, {1: "B", 2: "AC", 3: "B",
                                   4: "B", 5: "AC", 6: "C"})

    def test_解析原文不含答案行与分隔线(self):
        for q in self.questions:
            self.assertNotIn("答案：", q.note_raw, f"Q{q.no}")
            self.assertNotIn("---", q.note_raw, f"Q{q.no}")
            self.assertNotIn("**", q.note_raw, f"Q{q.no}")
            self.assertTrue(q.note_raw, f"Q{q.no}")

    def test_解析是完整一段(self):
        self.assertEqual(
            self.questions[3].note_raw,
            "鸿沟位于早期采用者与早期大众之间，是从早期市场进入主流市场的关键跨越。")


class TestCheckMock(unittest.TestCase):
    """模拟题的完整性自检：缺件或自相矛盾就停手，绝不猜。"""

    def _q(self, block):
        return m._parse_mock_block(block.split("\n"))

    def test_没有答案行时抛错(self):
        with self.assertRaises(m.ParseError) as ctx:
            self._q("**1.** 题干？\n\nA. 甲\nB. 乙\n\n解析：随便。")
        self.assertIn("Q1", str(ctx.exception))

    def test_答案字母不在选项里时抛错(self):
        with self.assertRaises(m.ParseError) as ctx:
            self._q("**1.** 题干？\n\nA. 甲\nB. 乙\n\n答案：C\n\n解析：随便。")
        self.assertIn("Q1", str(ctx.exception))

    def test_选项字母不连续时抛错(self):
        with self.assertRaises(m.ParseError) as ctx:
            self._q("**1.** 题干？\n\nA. 甲\nC. 丙\n\n答案：A\n\n解析：随便。")
        self.assertIn("Q1", str(ctx.exception))

    def test_多选标记与答案长度不一致时抛错(self):
        # 题干说多选、答案却只有一个字母 —— 多半是漏抄了，猜不出来
        with self.assertRaises(m.ParseError) as ctx:
            self._q("**1.** 题干？（多选）\n\nA. 甲\nB. 乙\n\n答案：A\n\n解析：随便。")
        self.assertIn("Q1", str(ctx.exception))

    def test_答案是多选但题干没标记时抛错(self):
        with self.assertRaises(m.ParseError) as ctx:
            self._q("**1.** 题干？\n\nA. 甲\nB. 乙\n\n答案：AB\n\n解析：随便。")
        self.assertIn("Q1", str(ctx.exception))

    def test_没有解析时抛错(self):
        with self.assertRaises(m.ParseError) as ctx:
            self._q("**1.** 题干？\n\nA. 甲\nB. 乙\n\n答案：A\n")
        self.assertIn("Q1", str(ctx.exception))

    def test_没有题干时抛错(self):
        with self.assertRaises(m.ParseError) as ctx:
            self._q("**1.** \n\nA. 甲\nB. 乙\n\n答案：A\n\n解析：随便。")
        self.assertIn("Q1", str(ctx.exception))

    def test_题干换行时抛错(self):
        # 题干写在两行上，第二行既不是选项也不是答案 —— 与其悄悄丢掉，不如报出来
        with self.assertRaises(m.ParseError) as ctx:
            self._q("**1.** 题干前半？\n后半？\n\nA. 甲\nB. 乙\n\n答案：A\n\n解析：随便。")
        self.assertIn("Q1", str(ctx.exception))

    def test_粘进来的多余行抛错(self):
        with self.assertRaises(m.ParseError) as ctx:
            self._q("**1.** 题干？\n\nA. 甲\nB. 乙\n\n| 表 | 格 |\n\n答案：A\n\n解析：随便。")
        self.assertIn("Q1", str(ctx.exception))

    def test_合格的一题能过(self):
        q = self._q("**1.** 题干？\n\nA. 甲\nB. 乙\n\n答案：B\n\n解析：随便。")
        self.assertEqual(q.answer, "B")
        self.assertEqual(q.stem, "题干？")

    def test_分隔线不进解析(self):
        q = self._q("**1.** 题干？\n\nA. 甲\nB. 乙\n\n答案：B\n\n解析：随便。\n\n---\n")
        self.assertEqual(q.note_raw, "随便。")


class TestSourceOf(unittest.TestCase):

    def test_章节题库用章节号(self):
        text = CHAPTER1.read_text(encoding="utf-8")
        self.assertEqual(m.source_of(CHAPTER1, text, "chapter"), ("1", "第1章"))

    def test_模拟题用文件名与一级标题(self):
        text = MOCK1.read_text(encoding="utf-8")
        self.assertEqual(m.source_of(MOCK1, text, "mock"),
                         ("mock-exam-1", "NPDP 模拟题 第一套"))

    def test_没有一级标题时退回文件名(self):
        self.assertEqual(m.source_of(MOCK1, "没有标题\n", "mock"),
                         ("mock-exam-1", "mock-exam-1"))

    def test_模拟题存成章节文件名时抛错(self):
        # 否则会拿到 npdp-1-* 的 id，盖掉真正的第 1 章
        text = MOCK1.read_text(encoding="utf-8")
        fake = ROOT / "docs" / "npdp" / "exercise" / "chapter-1.md"
        with self.assertRaises(m.ParseError) as ctx:
            m.source_of(fake, text, "mock")
        self.assertIn("撞车", str(ctx.exception))

    def test_章节题库存成普通文件名时抛错(self):
        text = CHAPTER1.read_text(encoding="utf-8")
        with self.assertRaises(m.ParseError):
            m.source_of(MOCK1, text, "chapter")


class TestMockRows(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = MOCK1.read_text(encoding="utf-8")
        cls.rows = m.convert(cls.text, chapter="mock-exam-1", fixes={},
                             source_label="NPDP 模拟题 第一套", fmt="mock")

    def test_6行(self):
        self.assertEqual(len(self.rows), 6)

    def test_字段齐全且顺序正确(self):
        for row in self.rows:
            self.assertEqual(tuple(row), m.FIELD_ORDER)
            self.assertEqual(len(row), 17)

    def test_id与来源(self):
        self.assertEqual(self.rows[0]["id"], "npdp-mock-exam-1-001")
        self.assertEqual(self.rows[5]["id"], "npdp-mock-exam-1-006")
        for row in self.rows:
            self.assertEqual(row["source"], "NPDP 模拟题 第一套")

    def test_选项与答案(self):
        row = self.rows[0]
        self.assertEqual(row["optionA"], "产品的目标市场规模与增长预期")
        self.assertEqual(row["optionD"], "产品的定价区间")
        self.assertEqual(row["answer"], "B")

    def test_选项EF为空(self):
        for row in self.rows:
            self.assertEqual(row["optionE"], "")
            self.assertEqual(row["optionF"], "")

    def test_逐选项解析全为空(self):
        # 模拟题的解析是整段散文，没有 ③ 那样的逐选项解析
        for row in self.rows:
            for letter in "ABCDEF":
                self.assertEqual(row["note" + letter], "", f"{row['id']}.{letter}")

    def test_note就是那段解析(self):
        for row in self.rows:
            self.assertTrue(row["note"].strip(), row["id"])
            self.assertNotIn("考点提炼：", row["note"], row["id"])

    def test_字段里没有裸换行和裸制表符(self):
        for row in self.rows:
            for k, v in row.items():
                self.assertNotIn("\n", v, f"{row['id']}.{k}")
                self.assertNotIn("\t", v, f"{row['id']}.{k}")

    def test_去重后没有重复题干(self):
        stems = [row["question"] for row in self.rows]
        self.assertEqual(len(stems), len(set(stems)))

    def test_note_extra可以追加(self):
        rows = m.convert(self.text, chapter="mock-exam-1",
                         fixes={2: {"note_extra": "补充一句。"}},
                         source_label="NPDP 模拟题 第一套", fmt="mock")
        self.assertTrue(rows[1]["note"].endswith("补充一句。"))

    def test_不传修复时行为不变(self):
        rows = m.convert(self.text, chapter="mock-exam-1", fixes={},
                         source_label="NPDP 模拟题 第一套", fmt="mock")
        self.assertEqual([r["note"] for r in rows],
                         [r["note"] for r in self.rows])


class TestMockTsv(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tsv, cls.rows = m.run(MOCK1)

    def test_6行17列(self):
        lines = self.tsv.rstrip("\n").split("\n")
        self.assertEqual(len(lines), 6)
        for line in lines:
            self.assertEqual(line.count("\t"), 16, line[:40])

    def test_首列是id且唯一(self):
        ids = [line.split("\t")[0] for line in self.tsv.rstrip("\n").split("\n")]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids[0], "npdp-mock-exam-1-001")

    def test_没有裸换行(self):
        self.assertEqual(self.tsv.count("\n"), 6)

    def test_每题都有题干和答案(self):
        for row in self.rows:
            self.assertTrue(row["question"].strip(), row["id"])
            self.assertTrue(row["answer"].strip(), row["id"])

    def test_答案都是合法字母(self):
        for row in self.rows:
            self.assertRegex(row["answer"], r"^[A-F]{1,6}$", row["id"])


class TestChapterFormatUnaffected(unittest.TestCase):
    """加了模拟题分支之后，章节题库那一路的结果必须一字不变。"""

    def test_章节题库仍走chapter分支(self):
        text = CHAPTER1.read_text(encoding="utf-8")
        questions = m.parse_questions(text)
        self.assertEqual(len(questions), 65)
        for q in questions:
            self.assertEqual(q.fmt, "chapter")

    def test_跑出来的tsv与仓库里的文件一致(self):
        tsv, rows = m.run(CHAPTER1)
        self.assertEqual(len(rows), 51)
        self.assertEqual(tsv, CHAPTER1.with_suffix(".tsv").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
