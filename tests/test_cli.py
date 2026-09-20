import json

from mcpsurface.cli import analyze


def test_flags_duplicate_and_missing_schema():
    findings = analyze({"tools": [
        {"name": "read", "description": "Read data", "inputSchema": {"type": "object"}},
        {"name": "read", "description": "Duplicate", "inputSchema": {"type": "object"}},
    ]})
    rules = {item.rule for item in findings}
    assert "MCP003" in rules


def test_flags_conflicting_annotations():
    findings = analyze({"tools": [
        {
            "name": "delete",
            "description": "Delete a record",
            "inputSchema": {"type": "object"},
            "annotations": {"readOnlyHint": True, "destructiveHint": True},
        }
    ]})
    assert any(item.rule == "MCP008" and item.severity == "error" for item in findings)


def test_clean_manifest_has_no_errors():
    findings = analyze({"tools": [
        {
            "name": "search",
            "description": "Search the local catalog",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False},
        }
    ]})
    assert not any(item.severity == "error" for item in findings)
