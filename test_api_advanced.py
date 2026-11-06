#!/usr/bin/python3
"""Offline regression tests for the API advanced project."""

import ast
import contextlib
import io
import os
import requests
import runpy
import unittest
from unittest.mock import Mock, patch


ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "api_advanced")
FILES = ["0-subs.py", "1-top_ten.py", "2-recurse.py", "3-count.py"]
NAMES = ["number_of_subscribers", "top_ten", "recurse", "count_words"]


def response(titles=None, after=None, status=200, data=None):
    """Build a Reddit-style mock response."""
    result = Mock()
    result.status_code = status
    if data is None:
        data = {"children": [{"data": {"title": title}}
                             for title in titles or []], "after": after}
    result.json.return_value = {"data": data}
    return result


class RedditTests(unittest.TestCase):
    """Verify the required function contracts using controlled listings."""

    def setUp(self):
        """Load functions without depending on user OAuth configuration."""
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.functions = [runpy.run_path(os.path.join(ROOT, filename))
                          .get(name) for filename, name in zip(FILES, NAMES)]

    def tearDown(self):
        """Restore the user's environment."""
        self.environment.stop()

    def capture(self, index, *args):
        """Capture standard output and the result of one function call."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = self.functions[index](*args)
        return result, output.getvalue()

    def test_subscribers(self):
        """Use subscribers rather than active user counts."""
        with patch("requests.get", return_value=response(
                data={"subscribers": 12345, "active_user_count": 42})) as get:
            self.assertEqual(self.capture(0, "programming"), (12345, ""))
        args, kwargs = get.call_args
        self.assertTrue(args[0].endswith("/r/programming/about.json"))
        self.assertFalse(kwargs.get("allow_redirects"))
        self.assertTrue(kwargs.get("headers").get("User-Agent"))
        self.assertNotIn("Authorization", kwargs.get("headers"))

    def test_invalid_and_redirects(self):
        """Never follow redirects or treat HTTP failures as valid data."""
        for status in (301, 302, 403, 404, 429, 500):
            for index in range(4):
                with patch("requests.get", return_value=response(
                        status=status)) as get:
                    args = ("invalid", ["python"]) if index == 3 else (
                        "invalid",)
                    result, output = self.capture(index, *args)
                if index == 1 and status not in (301, 302, 404):
                    # top_ten only reports None for redirects and 404s.
                    self.assertEqual(output, "")
                else:
                    self.assertEqual(output,
                                     "None\n" if index == 1 else "")
                self.assertEqual(result, 0 if index == 0 else None)
                self.assertFalse(get.call_args[1].get("allow_redirects"))

    def test_top_ten(self):
        """Print exactly the first ten titles in API order."""
        titles = ["Title {}".format(index) for index in range(12)]
        with patch("requests.get", return_value=response(titles)) as get:
            result, output = self.capture(1, "programming")
        self.assertIsNone(result)
        self.assertEqual(output, "\n".join(titles[:10]) + "\n")
        self.assertEqual(get.call_args[1].get("params").get("limit"), 10)

    def test_minimal_requests_interface(self):
        """Support test clients implementing the exercise's request options."""
        for status in (200, 404):
            for index in range(4):
                data = {"subscribers": 12} if index == 0 else {
                    "children": [{"data": {"title": "java"}}], "after": None}

                def get(url, headers=None, params=None, allow_redirects=True):
                    return response(status=status, data=data)

                with patch("requests.get", get):
                    args = ("test", ["java"]) if index == 3 else ("test",)
                    result, output = self.capture(index, *args)
                if status == 404:
                    self.assertEqual(result, 0 if index == 0 else None)
                    self.assertEqual(output, "None\n" if index == 1 else "")
                elif index == 0:
                    self.assertEqual((result, output), (12, ""))
                elif index == 1:
                    self.assertEqual((result, output), (None, "java\n"))
                elif index == 2:
                    self.assertEqual((result, output), (["java"], ""))
                else:
                    self.assertEqual((result, output), (None, "java: 1\n"))

    def test_recursive_pagination(self):
        """Follow every after cursor, including an empty intermediate page."""
        pages = [response(["First", "Second"], "t3_next"),
                 response([], "t3_last"), response(["Third"])]
        with patch("requests.get", side_effect=pages) as get:
            self.assertEqual(self.capture(2, "programming"),
                             (["First", "Second", "Third"], ""))
        self.assertEqual([call[1].get("params").get("after")
                          for call in get.call_args_list],
                         [None, "t3_next", "t3_last"])

    def test_independent_calls(self):
        """Default accumulators must not leak between calls."""
        with patch("requests.get", side_effect=[response(["One"]),
                                                response(["Two"])]):
            self.assertEqual(self.capture(2, "a"), (["One"], ""))
            self.assertEqual(self.capture(2, "b"), (["Two"], ""))

    def test_supplied_hot_list(self):
        """Honor a caller-supplied accumulator."""
        initial = ["Earlier"]
        with patch("requests.get", return_value=response(["Later"])):
            result, unused = self.capture(2, "programming", initial)
        self.assertIs(result, initial)
        self.assertEqual(result, ["Earlier", "Later"])

    def test_empty_listings(self):
        """Empty listings return None or print nothing as appropriate."""
        with patch("requests.get", side_effect=lambda *a, **k: response()):
            self.assertEqual(self.capture(2, "empty"), (None, ""))
            self.assertEqual(self.capture(3, "empty", ["java"]), (None, ""))

    def test_weighted_keyword_counts(self):
        """Count occurrences, duplicates, case, punctuation, and sort ties."""
        pages = [response(["Java java java. java! java_ javascript",
                           "PYTHON python react"], "t3_next"),
                 response(["JAVA JavaScript React"])]
        words = ["Java", "JAVA", "python", "javascript", "react", "absent"]
        with patch("requests.get", side_effect=pages) as get:
            self.assertEqual(self.capture(3, "programming", words),
                             (None, "java: 6\njavascript: 2\n"
                              "python: 2\nreact: 2\n"))
        self.assertEqual(get.call_args_list[1][1].get("params").get("after"),
                         "t3_next")
        self.assertEqual(words[0], "Java")

    def test_no_keyword_matches(self):
        """Do not print zero counts or match substrings and punctuation."""
        with patch("requests.get", return_value=response(
                ["javascript java. java! java_ other"])):
            self.assertEqual(self.capture(3, "programming", ["java"]),
                             (None, ""))

    def test_count_calls_are_independent(self):
        """Each keyword query starts with fresh counts."""
        with patch("requests.get", side_effect=[response(["java"]),
                                                response(["python"])]):
            self.assertEqual(self.capture(3, "a", ["java"]),
                             (None, "java: 1\n"))
            self.assertEqual(self.capture(3, "b", ["java"]), (None, ""))

    def test_errors(self):
        """Network and non-JSON responses use documented failure results."""
        for error in (requests.RequestException("offline"), ValueError()):
            for index in range(4):
                broken = response()
                broken.json.side_effect = error
                with patch("requests.get", return_value=broken):
                    args = ("test", ["java"]) if index == 3 else ("test",)
                    result, output = self.capture(index, *args)
                self.assertEqual(result, 0 if index == 0 else None)
                self.assertEqual(output, "None\n" if index == 1 else "")
        with patch("requests.get", side_effect=requests.Timeout("offline")):
            self.assertEqual(self.capture(0, "test"), (0, ""))

    def test_later_page_failure(self):
        """Do not present incomplete results when a later request fails."""
        for index in (2, 3):
            with patch("requests.get", side_effect=[
                    response(["java"], "t3_next"), response(status=429)]):
                args = ("test", ["java"]) if index == 3 else ("test",)
                self.assertEqual(self.capture(index, *args), (None, ""))

    def test_oauth_configuration(self):
        """Use OAuth only when a token is explicitly configured."""
        os.environ["REDDIT_ACCESS_TOKEN"] = "test-token"
        os.environ["REDDIT_USER_AGENT"] = "test-client/1.0"
        for index in (0, 2, 3):
            with patch("requests.get", return_value=response()) as get:
                args = ("test", ["java"]) if index == 3 else ("test",)
                self.capture(index, *args)
            self.assertTrue(get.call_args[0][0].startswith(
                "https://oauth.reddit.com/"))
            self.assertEqual(get.call_args[1].get("headers"), {
                "User-Agent": "test-client/1.0",
                "Authorization": "Bearer test-token"})

    def test_import_safety_and_source_requirements(self):
        """Check import safety, documentation, syntax, and real recursion."""
        with patch("requests.get") as get:
            for filename, name in zip(FILES, NAMES):
                path = os.path.join(ROOT, filename)
                with open(path, "rb") as stream:
                    source = stream.read()
                self.assertTrue(source.startswith(b"#!/usr/bin/python3\n"))
                self.assertTrue(source.endswith(b"\n"))
                self.assertNotIn(b"\r", source)
                tree = ast.parse(source)
                self.assertTrue(ast.get_docstring(tree))
                imports = [node.module if isinstance(node, ast.ImportFrom)
                           else node.names[0].name for node in tree.body
                           if isinstance(node, (ast.Import, ast.ImportFrom))]
                self.assertEqual(imports, sorted(imports))
                if name in ("recurse", "count_words"):
                    self.assertTrue(any(isinstance(node, ast.Call)
                                        and isinstance(node.func, ast.Name)
                                        and node.func.id == name
                                        for node in ast.walk(tree)))
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    runpy.run_path(path, run_name="import_check")
                self.assertEqual(output.getvalue(), "")
            self.assertEqual(get.call_count, 0)


if __name__ == "__main__":
    unittest.main()
