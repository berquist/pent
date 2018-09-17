r"""*Test objects for* ``pent`` *test suite*.

``pent`` Extracts Numerical Text.

**Author**
    Brian Skinn (bskinn@alum.mit.edu)

**File Created**
    3 Sep 2018

**Copyright**
    \(c) Brian Skinn 2018

**Source Repository**
    http://www.github.com/bskinn/pent

**Documentation**
    http://pent.readthedocs.io

**License**
    The MIT License; see |license_txt|_ for full license terms

**Members**

*(none documented)*

"""


import itertools as itt
import re
import unittest as ut


class SuperPent:
    """Superclass of various test classes, with common methods."""

    @staticmethod
    def does_parse_match(re_pat, s):
        """Run an individual parse test on `s` using regex pattern `re_pat`."""
        m = re.search(re_pat, s)

        return m is not None

    @staticmethod
    def make_testname(v, n, s):
        """Compose test name from a numerical value and pattern Number/Sign."""
        return "{0}_{1}_{2}".format(v, n, s)


class TestPentCorePatterns(ut.TestCase, SuperPent):
    """Confirming basic pattern matching of the core regex patterns."""

    def test_number_and_sign_matching(self):
        """Confirm number and sign patterns match the right string patterns."""
        import pent

        from .testdata import number_sign_vals as vals

        for (v, n, s) in itt.product(vals, pent.Number, pent.Sign):
            with self.subTest(self.make_testname(v, n, s)):
                npat = pent.number_patterns[(n, s)]
                npat = pent.std_wordify(npat)

                res = self.does_parse_match(npat, v)

                self.assertEqual(vals[v][(n, s)], res, msg=npat)

    def test_raw_single_value_space_delimited(self):
        """Confirm single-value parsing from a line works with raw patterns."""
        import pent

        from .testdata import number_sign_vals as vals

        test_line = "This line contains the value {} with space delimit."

        for v in vals:
            test_str = test_line.format(v)

            for (n, s) in itt.product(pent.Number, pent.Sign):
                with self.subTest(self.make_testname(v, n, s)):
                    npat = pent.number_patterns[(n, s)]
                    npat = pent.std_wordify(npat)

                    res = self.does_parse_match(npat, test_str)

                    self.assertEqual(vals[v][(n, s)], res, msg=test_str)


class TestPentParserPatterns(ut.TestCase, SuperPent):
    """Confirming pattern matching of patterns generated by the Parser."""

    import pent

    prs = pent.Parser()

    def test_group_tags_or_not(self):
        """Confirm group tags are added when needed; omitted when not."""
        import pent

        patterns = {
            pent.Content.Any: "~{}",
            pent.Content.String: "@{}.this",
            pent.Content.Number: "#{}..g",
        }

        for content, capture in itt.product(pent.Content, (True, False)):
            test_name = "{0}_{1}".format(content, capture)
            with self.subTest(test_name):
                test_pat = patterns[content].format("" if capture else "!")
                test_rx = self.prs.convert_line(test_pat)
                self.assertEqual(capture, "(?P<" in test_rx, msg=test_pat)

    def test_parser_single_line_space_delim(self):
        """Confirm parser works on single lines with space-delimited values.

        Also tests the 'suppress' number mode.

        """
        import pent

        from .testdata import number_sign_vals as vals

        test_line = "This line contains the value {} with space delimit."
        test_pat_template = "~! @.contains ~ #.{0}{1} ~!"

        for v in vals:
            test_str = test_line.format(v)

            for (n, s) in itt.product(pent.Number, pent.Sign):
                test_pat = test_pat_template.format(s.value, n.value)

                with self.subTest(self.make_testname(v, n, s)):
                    npat = self.prs.convert_line(test_pat)

                    res = self.does_parse_match(npat, test_str)

                    self.assertEqual(vals[v][n, s], res, msg=test_str)

    def test_string_capture(self):
        """Confirm string capture works when desired; is ignored when not."""
        import pent

        test_line = "This is a string with a word and [symbol] in it."
        test_pat_capture = "~! @.word ~!"
        test_pat_ignore = "~! @!.word ~!"
        test_pat_symbol = "~! @.[symbol] ~!"

        with self.subTest("capture"):
            pat = self.prs.convert_line(test_pat_capture)
            m = re.search(pat, test_line)
            self.assertIsNotNone(m)
            self.assertEqual(m.group(pent.group_prefix + "1"), "word")

        with self.subTest("ignore"):
            pat = self.prs.convert_line(test_pat_ignore)
            m = re.search(pat, test_line)
            self.assertIsNotNone(m)
            self.assertRaises(IndexError, m.group, pent.group_prefix + "1")

        with self.subTest("symbol"):
            pat = self.prs.convert_line(test_pat_symbol)
            m = re.search(pat, test_line)
            self.assertIsNotNone(m)
            self.assertEqual(m.group(pent.group_prefix + "1"), "[symbol]")

    def test_single_num_capture(self):
        """Confirm single-number capture works."""
        import pent

        from .testdata import number_sign_vals as vals

        test_line = "This is a string with {} in it."
        test_pat_template = "~! #.{0}{1} ~!"

        for v in vals:
            test_str = test_line.format(v)

            for (n, s) in itt.product(pent.Number, pent.Sign):
                test_pat = test_pat_template.format(s.value, n.value)

                with self.subTest(self.make_testname(v, n, s)):
                    npat = self.prs.convert_line(test_pat)

                    m = re.search(npat, test_str)

                    self.assertEqual(
                        vals[v][n, s], m is not None, msg=test_str
                    )

                    if m is not None:
                        self.assertEqual(m.group(pent.group_prefix + "1"), v)

    def test_single_nums_no_space(self):
        """Confirm two-number capture works, with no intervening space.

        Not a particularly real-world test-case, but it probes the
        no-space-before check.

        """
        import pent

        test_str = "This is a string with 123-456 in it."
        test_pat = "~! #x.+i #.-i ~!"

        npat = self.prs.convert_line(test_pat)

        m = re.search(npat, test_str)

        self.assertIsNotNone(m)
        self.assertEqual(m.group(pent.group_prefix + "1"), "123")
        self.assertEqual(m.group(pent.group_prefix + "2"), "-456")

    def test_single_num_preceding_colon_capture(self):
        """Confirm single-number capture works, with preceding colon."""
        import pent

        from .testdata import number_sign_vals as vals

        test_line = "This is a string with :{} in it, after a colon."
        test_pat_template = "~! @x!.: #.{0}{1} ~!"

        for v in vals:
            test_str = test_line.format(v)

            for (n, s) in itt.product(pent.Number, pent.Sign):
                test_pat = test_pat_template.format(s.value, n.value)

                with self.subTest(self.make_testname(v, n, s)):
                    npat = self.prs.convert_line(test_pat)

                    m = re.search(npat, test_str)

                    self.assertEqual(
                        vals[v][n, s], m is not None, msg=test_str
                    )

                    if m is not None:
                        self.assertEqual(m.group(pent.group_prefix + "1"), v)

    def test_string_and_single_num_capture(self):
        """Confirm multiple capture of string and single number."""
        import pent

        from .testdata import number_sign_vals as vals

        test_line = "This is a string with {} in it."
        test_pat_template = "~! @.string ~! #.{0}{1} ~!"

        for v in vals:
            test_str = test_line.format(v)

            for (n, s) in itt.product(pent.Number, pent.Sign):
                test_pat = test_pat_template.format(s.value, n.value)

                with self.subTest(self.make_testname(v, n, s)):
                    npat = self.prs.convert_line(test_pat)

                    m = re.search(npat, test_str)

                    self.assertEqual(
                        vals[v][n, s], m is not None, msg=test_str
                    )

                    if m is not None:
                        self.assertEqual(
                            m.group(pent.group_prefix + "1"), "string"
                        )
                        self.assertEqual(m.group(pent.group_prefix + "2"), v)

    def number_ending_sentence(self):
        """Check that a number at the end of a sentence matches correctly."""
        import pent

        from .testdata import number_patterns as npats

        test_line = "This sentence ends with a number {}."
        test_pat = "~! {} @!.."

        for n in npats:
            token = npats[n].format("", "", ".")
            with self.subTest(token):
                pat = test_pat.format(token)
                m = re.search(pat, test_line.format(n))

                self.assertIsNotNone(m, msg=token)
                self.assertEqual(n, m.group(pent.group_prefix + "1"))

    def test_match_entire_line(self):
        """Confirm the tilde works to match an entire line."""
        import pent

        test_line = "This is a line with whatever weird (*#$(*&23646{}}{#$"

        with self.subTest("capture"):
            pat = self.prs.convert_line("~")
            self.assertTrue(self.does_parse_match(pat, test_line))

            m = re.search(pat, test_line)
            self.assertEqual(test_line, m.group(pent.group_prefix + "1"))

        with self.subTest("no_capture"):
            pat = self.prs.convert_line("~!")
            self.assertTrue(self.does_parse_match(pat, test_line))

            m = re.search(pat, test_line)
            self.assertRaises(IndexError, m.group, pent.group_prefix + "1")

    def test_any_token_capture_ranges(self):
        """Confirm 'any' captures work as expected with other tokens."""
        import pent

        test_line_start = "This is a line "
        test_line_end = " with a number in brackets in the middle."
        test_num = "2e-4"
        test_line = test_line_start + "[" + test_num + "]" + test_line_end

        pat = pent.Parser().convert_line("~ @x!.[ #x..g @x!.] ~")
        m = re.search(pat, test_line)

        self.assertEqual(m.group(pent.group_prefix + "1"), test_line_start)
        self.assertEqual(m.group(pent.group_prefix + "2"), test_num)
        self.assertEqual(m.group(pent.group_prefix + "3"), test_line_end)

    def test_manual_two_lines(self):
        """Run manual check on concatenating two single-line regexes."""
        test_str = "This is line one: 12345  \nAnd this is line two: -3e-5"

        test_pat_1 = "~! @!.one: #!.+i"
        test_pat_2 = "~! @!.two: #!.-s"

        cp_1 = self.prs.convert_line(test_pat_1)
        cp_2 = self.prs.convert_line(test_pat_2)

        m = re.search(cp_1 + r"\n" + cp_2, test_str)

        self.assertIsNotNone(m)


class TestPentTokens(ut.TestCase, SuperPent):
    """Direct tests on the Token class."""

    def test_arbitrary_bad_token(self):
        """Confirm bad tokens raise errors."""
        import pent

        self.assertRaises(pent.BadTokenError, pent.Token, "abcd")

    def test_group_enclosures(self):
        """Ensure 'ignore' flag is properly set."""
        import pent

        testname_fmt = "{0}_{1}"
        token_fmt = {
            pent.Content.Any: "~{0}",
            pent.Content.String: "@{0}.thing",
            pent.Content.Number: "#{0}..i",
        }

        for c, i in itt.product(pent.Content, (True, False)):
            t = pent.Token(token_fmt[c].format("!" if i else ""))
            with self.subTest(testname_fmt.format(c, i)):
                self.assertEqual(t.ignore, i)

    def test_number_property(self):
        """Ensure t.number properties return correct values."""
        import pent

        from .testdata import number_patterns as npats

        for p in npats.values():
            pat = p.format("", "", pent.Quantity.Single)
            with self.subTest(pat):
                self.assertEqual(pent.Token(pat).number, pent.Number(p[-1]))

        with self.subTest("string"):
            self.assertEqual(pent.Token("@.abcd").number, None)

        with self.subTest("any"):
            self.assertEqual(pent.Token("~").number, None)

    def test_sign_property(self):
        """Ensure t.sign properties return correct values."""
        import pent

        from .testdata import number_patterns as npats

        for p in npats.values():
            pat = p.format("", "", pent.Quantity.Single)
            with self.subTest(pat):
                self.assertEqual(pent.Token(pat).sign, pent.Sign(p[-2]))

        with self.subTest("string"):
            self.assertEqual(pent.Token("@.abcd").sign, None)

        with self.subTest("any"):
            self.assertEqual(pent.Token("~").sign, None)


class TestPentParserPatternsSlow(ut.TestCase, SuperPent):
    """SLOW tests confirming pattern matching of Parser regexes."""

    import pent

    prs = pent.Parser()

    def test_three_token_sequence(self):
        """Ensure combinatorial token sequence parses correctly."""
        import pent

        from .testdata import number_patterns as nps

        pat_template = "~! {0} {1} {2} ~!"
        str_template = "String! {0}{1}{2}{3}{4} More String!"
        str_pat = {"foo": "@{0}{1}{2}foo"}

        testname_template = "{0}_{1}_{2}_{3}_{4}"

        str_or_num = (pent.Content.String, pent.Content.Number)
        t_f = (True, False)

        for c1, s1, c2, s2, c3 in itt.product(
            str_or_num, t_f, str_or_num, t_f, str_or_num
        ):
            if (c1 is c2 and not s1) or (c2 is c3 and not s2):
                # No reason to have no-space strings against one another;
                # no-space numbers adjacent to one another make
                # no syntactic sense.
                continue

            vals1 = str_pat if c1 == pent.Content.String else nps.keys()
            vals2 = str_pat if c2 == pent.Content.String else nps.keys()
            vals3 = str_pat if c3 == pent.Content.String else nps.keys()

            for v1, v2, v3 in itt.product(vals1, vals2, vals3):
                p1 = (str_pat if c1 == pent.Content.String else nps)[
                    v1
                ].format(
                    pent.parser._s_no_space if not s1 else "",
                    "",
                    pent.Quantity.Single,
                )
                p2 = (str_pat if c2 == pent.Content.String else nps)[
                    v2
                ].format(
                    pent.parser._s_no_space if not s2 else "",
                    "",
                    pent.Quantity.Single,
                )
                p3 = (str_pat if c3 == pent.Content.String else nps)[
                    v3
                ].format("", "", pent.Quantity.Single)

                test_pat = pat_template.format(p1, p2, p3)
                test_str = str_template.format(
                    v1, " " if s1 else "", v2, " " if s2 else "", v3
                )

                with self.subTest(
                    testname_template.format(v1, s1, v2, s2, v3)
                ):
                    npat = self.prs.convert_line(test_pat)

                    m = re.search(npat, test_str)

                    self.assertIsNotNone(m, msg=test_pat)
                    self.assertEqual(
                        m.group(pent.group_prefix + "1"),
                        v1,
                        msg=test_pat + " :: " + test_str,
                    )
                    self.assertEqual(
                        m.group(pent.group_prefix + "2"),
                        v2,
                        msg=test_pat + " :: " + test_str,
                    )
                    self.assertEqual(
                        m.group(pent.group_prefix + "3"),
                        v3,
                        msg=test_pat + " :: " + test_str,
                    )


def suite_base():
    """Create and return the test suite for base tests."""
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests(
        [
            tl.loadTestsFromTestCase(TestPentCorePatterns),
            tl.loadTestsFromTestCase(TestPentParserPatterns),
            tl.loadTestsFromTestCase(TestPentTokens),
        ]
    )
    return s


def suite_base_slow():
    """Create and return the test suite for SLOW base tests."""
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestPentParserPatternsSlow)])
    return s


if __name__ == "__main__":
    print("Module not executable.")
