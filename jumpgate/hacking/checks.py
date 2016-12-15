import re

"""
Guidelines for writing new hacking checks
 - Pick numbers in the range J3xx. Find the current test with
   the highest allocated number and then pick the next value.
 - Keep the test method code in the source file ordered based
   on the J3xx value.
 - List the new rule in the top level HACKING.rst file
 - Add test cases for each new rule to jumpgate/tests/unit/test_hacking.py
"""

assert_trueinst_re = re.compile(
    r"(.)*assertTrue\(isinstance\((\w|\.|\'|\"|\[|\])+, "
    "(\w|\.|\'|\"|\[|\])+\)\)")

# Matches both assertEqual(type(foo), bar) and assertEqual(bar, type(foo))
assert_equal_type_re = re.compile(
    r"(.)*assertEqual\(((type\((\w|\.|\'|\"|\[|\])+\), "
    "(\w|\.|\'|\"|\[|\])+)|"
    "((\w|\.|\'|\"|\[|\])+, type\((\w|\.|\'|\"|\[|\])+\)))\)")

assert_true_false_with_in_or_not_in = re.compile(
    r"assert(True|False)\("
    r"(\w|[][.'\"])+( not)? in (\w|[][.'\",])+(, .*)?\)")
assert_true_false_with_in_or_not_in_spaces = re.compile(
    r"assert(True|False)"
    r"\((\w|[][.'\"])+( not)? in [\[|'|\"](\w|[][.'\", ])+"
    r"[\[|'|\"](, .*)?\)")

assert_equal_in_end_with_true_or_false_re = re.compile(
    r"assertEqual\("
    r"(\w|[][.'\"])+ in (\w|[][.'\", ])+, (True|False)\)")
assert_equal_in_start_with_true_or_false_re = re.compile(
    r"assertEqual\("
    r"(True|False), (\w|[][.'\"])+ in (\w|[][.'\", ])+\)")


def assert_true_instance(logical_line):
    """Check for assertTrue(isinstance(a, b)) statements

    J301
    """
    if assert_trueinst_re.match(logical_line):
        yield (0, "J301: assertIsInstance(a, b) must be used instead of"
                  " assertTrue(isinstance(a, b))")


def assert_equal_type(logical_line):
    """Check for assertEqual(type(A), B) statements

    J302
    """
    if assert_equal_type_re.match(logical_line):
        yield (0, "J302: assertIsInstance(a, b) must be used instead of"
                  " assertEqual(type(a), b)")


def assert_equal_none(logical_line):
    """Check for assertEqual(A, None) or assertEqual(None, A) sentences

    J303
    """
    _start_re = re.compile(r"assertEqual\(.*?,\s+None\)$")
    _end_re = re.compile(r"assertEqual\(None,")

    if _start_re.search(logical_line) or _end_re.search(logical_line):
        yield (0, "J303: assertEqual(A, None) or assertEqual(None, A) "
               "sentences not allowed. Use assertIsNone(A) instead.")

    _start_re = re.compile(r"assertIs(Not)?\(None,")
    _end_re = re.compile(r"assertIs(Not)?\(.*,\s+None\)$")

    if _start_re.search(logical_line) or _end_re.search(logical_line):
        yield (0, "J303: assertIsNot(A, None) or assertIsNot(None, A) must "
               "not be used. Use assertIsNone(A) or assertIsNotNone(A) "
               "instead.")


def assert_true_or_false_with_in(logical_line):
    """Check for assertTrue/False on collections.

    This includes: assertTrue/False(A in B), assertTrue/False(A not in B),
    assertTrue/False(A in B, message) or assertTrue/False(A not in B, message)
    sentences.

    J304
    """
    res = (assert_true_false_with_in_or_not_in.search(logical_line) or
           assert_true_false_with_in_or_not_in_spaces.search(logical_line))
    if res:
        yield (0, "J304: Use assertIn/NotIn(A, B) rather than "
                  "assertTrue/False(A in/not in B) when checking collection "
                  "contents.")


def assert_equal_in(logical_line):
    """Check for assertEqual with True and collections.

    This includes: assertEqual(A in B, True), assertEqual(True, A in B),
    assertEqual(A in B, False) or assertEqual(False, A in B) sentences

    J305
    """
    res = (assert_equal_in_start_with_true_or_false_re.search(logical_line) or
           assert_equal_in_end_with_true_or_false_re.search(logical_line))
    if res:
        yield (0, "J305: Use assertIn/NotIn(A, B) rather than "
                  "assertEqual(A in B, True/False) when checking collection "
                  "contents.")


def factory(register):
    register(assert_true_instance)
    register(assert_equal_type)
    register(assert_equal_none)
    register(assert_true_or_false_with_in)
    register(assert_equal_in)
