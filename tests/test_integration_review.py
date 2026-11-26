"""Consistency checks for the cleeng-integration-review skill and its evaluation fixtures.

The skill has no scripts. Its fixtures are run by hand in an agent (tests/fixtures/integrations/README.md);
these tests keep the rule index, the reference files and EXPECTED.json in step.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFERENCES = ROOT / "skills" / "cleeng-integration-review" / "references"
FIXTURES = ROOT / "tests" / "fixtures" / "integrations"


def index_rules() -> dict[str, str]:
    text = (REFERENCES / "rules-index.md").read_text(encoding="utf-8")
    return dict(re.findall(r"^\| ([A-Z]+-\d{2}) \|.*\| `([a-z-]+\.md)` \|$", text, re.M))


class IntegrationReviewTest(unittest.TestCase):
    def test_rule_index_matches_rule_sections(self):
        sections = {
            rule: path.name
            for path in REFERENCES.glob("*.md")
            for rule in re.findall(r"^## ([A-Z]+-\d{2}) ", path.read_text(encoding="utf-8"), re.M)
        }
        self.assertEqual(index_rules(), sections)

    def test_expected_findings_point_at_real_lines(self):
        expected = json.loads((FIXTURES / "EXPECTED.json").read_text(encoding="utf-8"))
        rules = index_rules()
        self.assertEqual(set(expected), {p.name for p in FIXTURES.iterdir() if p.is_dir()})
        for fixture, findings in expected.items():
            for item in findings:
                self.assertIn(item["rule"], rules, f"{fixture}: unknown rule {item['rule']}")
                lines = (FIXTURES / fixture / item["file"]).read_text(encoding="utf-8").splitlines()
                self.assertTrue(lines[item["line"] - 1].strip(), f"{fixture}: {item['file']}:{item['line']} is blank")


if __name__ == "__main__":
    unittest.main()
