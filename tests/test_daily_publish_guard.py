import json
import tempfile
import unittest
from pathlib import Path
from scripts.check_daily_delivery import check_delivery

DATE = "2026-10-23"
POST = """---
layout: post
title: "Agent Infra Daily"
date: 2026-10-23 08:30:00 +0800
summary: "Daily strategic research and engineering takeaways"
tags: [agent-infra]
---
## 今日核心判断

""" + ("Substantive grounded analysis. " * 115) + "\n## Sources\nhttps://official.example/original\n"
DELTA = {"date": DATE, "mode": "daily",
         "nodes_added": [], "nodes_updated": [], "edges_added": [], "edges_updated": []}

class DeliveryGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        post = self.root / "_posts"
        delta = self.root / "_data/kg/deltas"
        post.mkdir(parents=True)
        delta.mkdir(parents=True)
        (post / f"{DATE}-agent-infra-daily.md").write_text(POST, encoding="utf-8")
        (delta / f"{DATE}.json").write_text(json.dumps(DELTA), encoding="utf-8")
    def tearDown(self):
        self.tmp.cleanup()
    def test_post_and_delta_pass_local_validation(self):
        result = check_delivery(self.root, DATE)
        self.assertTrue(result["passed"])
        self.assertEqual(result["pages"]["status"], "not_checked")
    def test_missing_delta_fails(self):
        (self.root / f"_data/kg/deltas/{DATE}.json").unlink()
        result = check_delivery(self.root, DATE)
        self.assertFalse(result["passed"])
        self.assertTrue(any("missing KG delta" in x for x in result["errors"]))
    def test_bad_post_front_matter_fails(self):
        (self.root / f"_posts/{DATE}-agent-infra-daily.md").write_text(
            POST.replace("summary:", "subtitle:"), encoding="utf-8")
        self.assertFalse(check_delivery(self.root, DATE)["passed"])
    def test_pages_requires_current_head_success(self):
        successful = {"workflow_runs": [{
            "name":"pages build and deployment", "id":987, "head_sha":"abc",
            "status":"completed", "conclusion":"success"}]}
        self.assertTrue(check_delivery(self.root, DATE, successful, "abc")["passed"])
        self.assertFalse(check_delivery(self.root, DATE, successful, "def")["passed"])
        bad = {"workflow_runs": [{**successful["workflow_runs"][0],
                                 "conclusion": "failure"}]}
        self.assertFalse(check_delivery(self.root, DATE, bad, "abc")["passed"])
        pending = {"workflow_runs": [{**successful["workflow_runs"][0],
                                     "status":"in_progress", "conclusion": None}]}
        self.assertFalse(check_delivery(self.root, DATE, pending, "abc")["passed"])

if __name__ == "__main__":
    unittest.main()
