"""Testes de fumaça do TripWatch AI (stdlib unittest).

Rodar:  python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime

_TMP = tempfile.mkdtemp(prefix="tripwatch-test-")
os.environ["TRIPWATCH_DB"] = os.path.join(_TMP, "test.db")
os.environ["TRIPWATCH_DISABLE_SCHEDULER"] = "1"
os.environ["TRIPWATCH_PROVIDER"] = "demo"

import agent  # noqa: E402
import app  # noqa: E402
import db  # noqa: E402
import engine  # noqa: E402


class TripWatchSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        db.seed(force=True)

    def test_seed_creates_demo_watchlists(self):
        watches = db.list_watches()
        self.assertEqual(len(watches), 11)
        self.assertEqual(sum(1 for w in watches if w["kind"] == "flight"), 4)
        self.assertEqual(sum(1 for w in watches if w["kind"] == "hotel"), 7)
        for watch in watches:
            self.assertGreater(len(watch["snapshots"]), 10)
            self.assertGreater(watch["last_price"], 0)

    def test_analysis_produces_recommendation(self):
        watch = db.list_watches()[0]
        analysis = agent.analyze(watch)
        self.assertIn(analysis["recommendation"], {"buy", "wait", "watch"})
        self.assertGreater(analysis["confidence"], 0)
        self.assertGreater(len(analysis["reasons"]), 0)
        self.assertGreater(analysis["points"], 10)

    def test_run_check_persists_snapshot(self):
        watch = db.list_watches()[0]
        before = len(watch["snapshots"])
        result = engine.run_check(watch["id"], force=True)
        self.assertTrue(result["ok"])
        self.assertGreater(result["price"], 0)
        after = next(w for w in db.list_watches() if w["id"] == watch["id"])
        self.assertEqual(len(after["snapshots"]), before + 1)

    def test_create_watch_from_payload(self):
        payload = {
            "kind": "flight", "origin": "the", "destination": "lis",
            "depart_date": "2027-03-10", "return_date": "2027-03-17",
            "target_price": 4000, "interval_minutes": 120,
        }
        watch = app.create_watch_from_payload(payload)
        self.assertEqual(watch["origin"], "THE")
        self.assertEqual(watch["destination"], "LIS")
        self.assertEqual(watch["interval_minutes"], 120)
        self.assertIn("THE → LIS", watch["title"])
        result = app.run_check_and_brief(watch["id"])
        self.assertIn("analysis", result)

    def test_city_route_parsing(self):
        self.assertEqual(agent._extract_route("Teresina → Lisboa"), ("THE", "LIS"))
        self.assertEqual(agent._extract_route("de Miami para Paris"), ("MIA", "CDG"))
        self.assertIsNone(agent._extract_route("hotel em Lisboa"))

    def test_target_price_parsing(self):
        self.assertEqual(agent._extract_target("abaixo de r$ 4.300"), 4300)
        self.assertEqual(agent._extract_target("ate r$ 1.250,50"), 1250.5)
        self.assertEqual(agent._extract_target("target 3000"), 3000)

    def test_chat_creates_watchlist(self):
        response = agent.chat("Monitore THE → LIS em 15/12, abaixo de R$ 4.300")
        self.assertIn("Pronto", response["answer"])
        watch_id = response.get("watch_id")
        self.assertTrue(watch_id)
        watch = db.get_watch(watch_id)
        self.assertEqual(watch["target_price"], 4300)
        self.assertEqual(watch["depart_date"][:4], str(datetime.now().year))

    def test_mcp_initialize_and_tools(self):
        init = app.handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(init["result"]["serverInfo"]["name"], "tripwatch-ai")
        tools = app.handle_mcp({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = [t["name"] for t in tools["result"]["tools"]]
        self.assertIn("track_flight", names)
        self.assertIn("travel_briefing", names)
        self.assertIn("agent_chat", names)

    def test_mcp_tool_call(self):
        result = app.mcp_call_tool("list_watchlist", {})
        self.assertGreaterEqual(len(result["watches"]), 5)
        briefing = app.mcp_call_tool("travel_briefing", {})
        self.assertIn("text", briefing)
        self.assertIn("stats", briefing)
        chat = app.mcp_call_tool("agent_chat", {"message": "Me mostre os alertas"})
        self.assertIn("answer", chat)

    def test_state_payload_shape(self):
        state = app.state_payload()
        for key in ("watches", "alerts", "repos", "settings", "provider", "scheduler", "briefing", "stats"):
            self.assertIn(key, state)
        self.assertIn("potential_savings", state["stats"])
        self.assertIn("repos", state["stats"])
        self.assertIn("text", state["briefing"])

    def test_repo_catalog_has_letsfg(self):
        repos = db.list_repos()
        letsfg = next((r for r in repos if r["name"] == "LetsFG/LetsFG"), None)
        self.assertIsNotNone(letsfg)
        self.assertIn("letsfg.co/mcp", letsfg["mcp_url"])
        self.assertIn("pip install letsfg", letsfg["install_cmd"])
        self.assertGreaterEqual(len(repos), 10)

    def test_add_repo_upsert(self):
        db.add_repo({"name": "Teste/Repo", "url": "https://github.com/teste/repo", "stars": 5, "license": "MIT"})
        db.add_repo({"name": "Teste/Repo", "url": "https://github.com/teste/repo", "stars": 9, "license": "MIT"})
        repo = next(r for r in db.list_repos() if r["url"] == "https://github.com/teste/repo")
        self.assertEqual(repo["stars"], 9)

    def test_mcp_list_repos(self):
        result = app.mcp_call_tool("list_repos", {})
        self.assertGreaterEqual(result["count"], 10)
        self.assertIn("LetsFG/LetsFG", [r["name"] for r in result["repos"]])

    def test_mcp_unknown_tool_returns_error(self):
        with self.assertRaises(ValueError):
            app.mcp_call_tool("nao_existe", {})


if __name__ == "__main__":
    unittest.main()
