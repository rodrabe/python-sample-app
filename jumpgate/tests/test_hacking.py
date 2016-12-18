import unittest

from jumpgate.hacking import checks


class HackingTestCase(unittest.TestCase):
    """This class tests the hacking checks in jumpgate.hacking.checks.

    It passes strings to the check methods like the pep8/flake8 parser would.
    The parser loops over each line in the file and then passes the parameters
    to the check method. The parameter names in the check method dictate what
    type of object is passed to the check method. The parameter types are::

        logical_line: A processed line with the following modifications:
            - Multi-line statements converted to a single line.
            - Stripped left and right.
            - Contents of strings replaced with "xxx" of same length.
            - Comments removed.
        physical_line: Raw line of text from the input file.
        lines: a list of the raw lines from the input file
        tokens: the tokens that contribute to this logical line
        line_number: line number in the input file
        total_lines: number of lines in the input file
        blank_lines: blank lines before this one
        indent_char: indentation character in this file (" " or "\t")
        indent_level: indentation (with tabs expanded to multiples of 8)
        previous_indent_level: indentation on previous line
        previous_logical: previous logical line
        filename: Path of the file being run through pep8

    When running a test on a check method the return will be False/None if
    there is no violation in the sample input. If there is an error a tuple is
    returned with a position in the line, and a message. So to check the result
    just assertTrue if the check is expected to fail and assertFalse if it
    should pass.
    """

    def test_assert_true_instance(self):
        self.assertEqual(len(list(checks.assert_true_instance(
            "self.assertTrue(isinstance(e, "
            "exception.BuildAbortException))"))), 1)

        self.assertEqual(
            list(checks.assert_true_instance(
                "self.assertTrue(False)")), [])

        self.assertEqual(
            list(checks.assert_true_instance(
                "self.assertIsInstance(e, "
                "exception.BuildAbortException))")), [])

    def test_assert_equal_type(self):
        self.assertEqual(len(list(checks.assert_equal_type(
            "self.assertEqual(type(als['QuicAssist']), list)"))), 1)

        self.assertEqual(len(list(checks.assert_equal_type(
            "self.assertEqual(list, type(als['QuicAssist']))"))), 1)

        self.assertEqual(list(checks.assert_equal_type(
            "self.assertEqual(foo, bar)")), [])

        self.assertEqual(list(checks.assert_equal_type(
            "self.assertIsInstance(foo, bar)")), [])

    def test_assert_equal_none(self):
        self.assertEqual(len(list(checks.assert_equal_none(
            "self.assertEqual(A, None)"))), 1)

        self.assertEqual(len(list(checks.assert_equal_none(
            "self.assertEqual(None, A)"))), 1)

        self.assertEqual(
            list(checks.assert_equal_none("self.assertIsNone()")), [])

        self.assertEqual(len(list(checks.assert_equal_none(
            "self.assertIs(A, None)"))), 1)

        self.assertEqual(len(list(checks.assert_equal_none(
            "self.assertIsNot(A, None)"))), 1)

        self.assertEqual(len(list(checks.assert_equal_none(
            "self.assertIs(None, A)"))), 1)

        self.assertEqual(len(list(checks.assert_equal_none(
            "self.assertIsNot(None, A)"))), 1)

    def test_assert_true_or_false_with_in_or_not_in(self):
        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertTrue(A in B)"))), 1)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertFalse(A in B)"))), 1)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertTrue(A not in B)"))), 1)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertFalse(A not in B)"))), 1)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertTrue(A in B, 'some message')"))), 1)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertFalse(A in B, 'some message')"))), 1)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertTrue(A not in B, 'some message')"))), 1)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertFalse(A not in B, 'some message')"))), 1)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertTrue(A in 'some string with spaces')"))), 1)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertTrue(A in ['1', '2', '3'])"))), 1)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertTrue(A in [1, 2, 3])"))), 1)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertTrue(any(A > 5 for A in B))"))), 0)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertTrue(any(A > 5 for A in B), 'some message')"))), 0)

        self.assertEqual(len(list(checks.assert_true_or_false_with_in(
            "self.assertFalse(some in list1 and some2 in list2)"))), 0)

    def test_assert_equal_in(self):
        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual(a in b, True)"))), 1)

        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual('str' in 'string', True)"))), 1)

        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual(any(a==1 for a in b), True)"))), 0)

        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual(True, a in b)"))), 1)

        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual(True, 'str' in 'string')"))), 1)

        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual(True, any(a==1 for a in b))"))), 0)

        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual(a in b, False)"))), 1)

        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual('str' in 'string', False)"))), 1)

        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual(any(a==1 for a in b), False)"))), 0)

        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual(False, a in b)"))), 1)

        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual(False, 'str' in 'string')"))), 1)

        self.assertEqual(len(list(checks.assert_equal_in(
            "self.assertEqual(False, any(a==1 for a in b))"))), 0)
