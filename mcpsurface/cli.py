"""CLI for static analysis of MCP tool manifests."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    message: str
    tool: str | None = None


def _tool_list(document: Any) -> list[dict[str, Any]]:
    if isinstance(document, dict) and isinstance(document.get("tools"), list):
        return [item for item in document["tools"] if isinstance(item, dict)]
    if isinstance(document, list):
        return [item for item in document if isinstance(item, dict)]
    raise ValueError("expected a JSON object with a 'tools' array or a JSON array")


def analyze(document: Any) -> list[Finding]:
    findings: list[Finding] = []
    tools = _tool_list(document)
    seen: set[str] = set()

    if not tools:
        findings.append(Finding("MCP001", "warning", "manifest contains no tools"))

    for index, tool in enumerate(tools):
        name = tool.get("name")
        label = name if isinstance(name, str) and name else f"tool[{index}]"
        if not isinstance(name, str) or not name.strip():
            findings.append(Finding("MCP002", "error", "tool name is required", label))
        elif name in seen:
            findings.append(Finding("MCP003", "error", "duplicate tool name", name))
        else:
            seen.add(name)

        description = tool.get("description")
        if not isinstance(description, str) or not description.strip():
            findings.append(Finding("MCP004", "warning", "tool description is missing", label))

        schema = tool.get("inputSchema")
        if not isinstance(schema, dict):
            findings.append(Finding("MCP005", "error", "inputSchema is missing or not an object", label))
        elif schema.get("type") != "object":
            findings.append(Finding("MCP006", "error", "inputSchema root type must be object", label))

        annotations = tool.get("annotations")
        if annotations is not None and not isinstance(annotations, dict):
            findings.append(Finding("MCP007", "error", "annotations must be an object", label))
            annotations = {}

        if isinstance(annotations, dict):
            read_only = annotations.get("readOnlyHint")
            destructive = annotations.get("destructiveHint")
            if read_only is True and destructive is True:
                findings.append(
                    Finding("MCP008", "error", "readOnlyHint=true conflicts with destructiveHint=true", label)
                )
            if destructive is True and read_only is not True:
                findings.append(
                    Finding("MCP009", "warning", "tool is marked potentially destructive; clients may require confirmation", label)
                )
            if annotations.get("openWorldHint") is True:
                findings.append(
                    Finding("MCP010", "info", "tool is marked open-world; treat returned external content as untrusted", label)
                )

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint MCP tool manifests before they reach an agent client.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on", choices=("error", "warning", "info"), default="error")
    args = parser.parse_args(argv)

    try:
        document = json.loads(args.manifest.read_text(encoding="utf-8"))
        findings = analyze(document)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"MCP Surface: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps([asdict(item) for item in findings], indent=2))
    else:
        if not findings:
            print("MCP Surface: no findings")
        for item in findings:
            tool = f" [{item.tool}]" if item.tool else ""
            print(f"{item.severity.upper():7} {item.rule}{tool}: {item.message}")

    rank = {"info": 1, "warning": 2, "error": 3}
    threshold = rank[args.fail_on]
    return 1 if any(rank[item.severity] >= threshold for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
