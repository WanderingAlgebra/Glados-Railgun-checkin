import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import checkin


class CheckinTests(unittest.TestCase):
    def test_response_classification(self):
        cases = [
            ({"code": 0, "points": 1, "message": "OK"}, checkin.CheckinStatus.SUCCESS),
            ({"code": 1, "message": "Checkin Repeats! Please Try Tomorrow"}, checkin.CheckinStatus.REPEAT),
            ({"code": 1, "message": "not logged in"}, checkin.CheckinStatus.FAILURE),
            ({"code": 4, "message": "device-mismatch"}, checkin.CheckinStatus.FAILURE),
            (None, checkin.CheckinStatus.FAILURE),
        ]
        with checkin.API("glados.rocks") as api:
            for response, expected in cases:
                with self.subTest(response=response):
                    self.assertEqual(api._parse_checkin(response)["code"], expected)

    def test_missing_cookie_fails(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(checkin.main(), 1)

    def test_result_exit_codes(self):
        cases = [
            ([checkin.CheckinStatus.SUCCESS], 0),
            ([checkin.CheckinStatus.REPEAT], 0),
            ([checkin.CheckinStatus.SUCCESS, checkin.CheckinStatus.FAILURE], 1),
            ([], 1),
        ]
        with patch.dict(os.environ, {"GLADOS_COOKIES": "test-cookie"}, clear=True):
            for statuses, expected in cases:
                with self.subTest(statuses=statuses), patch.object(checkin, "Checker") as checker:
                    checker.return_value.results = [SimpleNamespace(code=s) for s in statuses]
                    checker.return_value.format_results.return_value = ("test", "", "")
                    self.assertEqual(checkin.main(), expected)

    def test_config_exception_fails(self):
        with patch.object(checkin, "Config", side_effect=ValueError("invalid config")):
            self.assertEqual(checkin.main(), 1)


if __name__ == "__main__":
    unittest.main()
