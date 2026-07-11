#!/usr/bin/env python3
"""code_intel.py — CodeLens MCP wrapper for the pipeline's PLAN/EVALUATE stages.

Gives BUILD/PLAN a real dependency graph & blast radius instead of guesses.
Pure stdlib (urllib) so it runs anywhere the pipeline runs (incl. script crons).

Usage:
  python code_intel.py impact         --package owner/repo --symbol NAME
  python code_intel.py affected-tests --package owner/repo --symbol NAME
  python code_intel.py symbol         --package owner/repo --query  NAME
  python code_intel.py context        --package owner/repo --symbol NAME

Env overrides: CODELENS_URL, CODELENS_TOKEN.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

CF = os.environ.get("CODELENS_URL", "https://d1t9q5qxrql3xj.cloudfront.net/mcp/")
# Token is NEVER hardcoded — read from env (source ~/.meshclaw/secrets/codelens.env first).
TOKEN = os.environ.get("CODELENS_TOKEN", "")


def _sse(text: str) -> dict:
    for line in text.splitlines():
        if line.startswith("data:"):
            try:
                return json.loads(line[5:].strip())
            except Exception:
                pass
    try:
        return json.loads(text)
    except Exception:
        return {}


def _post(headers: dict, payload: dict) -> "tuple[dict, dict]":
    data = json.dumps(payload).encode()
    req = urllib.request.Request(CF, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode()
        return _sse(body), dict(resp.headers)


def mcp_call(tool: str, arguments: dict) -> dict:
    """One JSON-RPC session: initialize -> initialized -> tools/call."""
    if not TOKEN:
        return {"error": "CODELENS_TOKEN not set — run: source ~/.meshclaw/secrets/codelens.env"}
    h = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
         "Accept": "application/json, text/event-stream"}
    _, resp_headers = _post(h, {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "pipeline-code-intel", "version": "1"}},
    })
    sid = resp_headers.get("mcp-session-id") or resp_headers.get("Mcp-Session-Id")
    if sid:
        h["mcp-session-id"] = sid
    _post(h, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    result, _ = _post(h, {
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    })
    if "error" in result:
        return {"error": result["error"]}
    sc = result.get("result", {}).get("structuredContent", {})
    inner = sc.get("result", sc)
    if isinstance(inner, str):
        try:
            return json.loads(inner)
        except Exception:
            return {"raw": inner}
    return inner


def main() -> None:
    ap = argparse.ArgumentParser(description="CodeLens blast-radius feed for the pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("impact", "affected-tests", "context"):
        p = sub.add_parser(name)
        p.add_argument("--package", required=True)
        p.add_argument("--symbol", required=True)
    p = sub.add_parser("symbol")
    p.add_argument("--package", required=True)
    p.add_argument("--query", required=True)

    args = ap.parse_args()
    tool_map = {
        "impact": ("get_impact", {"package_name": args.package, "target": getattr(args, "symbol", None)}),
        "affected-tests": ("find_affected_tests", {"package_name": args.package, "target": getattr(args, "symbol", None)}),
        "context": ("build_context", {"package_name": args.package, "target": getattr(args, "symbol", None)}),
        "symbol": ("find_symbol", {"package_name": args.package, "query": getattr(args, "query", None)}),
    }
    tool, arguments = tool_map[args.cmd]
    print(json.dumps(mcp_call(tool, arguments), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
