import unittest

from gui.country_manager import (
    country_for_code,
    tor_exit_preference,
    validate_country_code,
)


class CountryManagerTests(unittest.TestCase):
    def test_country_selection_is_a_tor_exit_preference(self):
        self.assertEqual(validate_country_code(" DE "), "de")
        self.assertEqual(country_for_code("de").name, "Germany")
        self.assertEqual(tor_exit_preference("de"), ("ExitNodes {de}",))
        self.assertEqual(tor_exit_preference(""), ())

    def test_unknown_or_malformed_country_is_rejected(self):
        for code in ("d", "de1", "zz"):
            with self.subTest(code=code), self.assertRaises(ValueError):
                validate_country_code(code)


if __name__ == "__main__":
    unittest.main()
