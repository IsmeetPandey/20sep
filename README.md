# MCP Surface

Static risk and quality linting for **Model Context Protocol (MCP)** tool manifests.

MCP tool metadata includes input/output schemas and behavioral hints such as `readOnlyHint`, `destructiveHint`, `idempotentHint`, and `openWorldHint`. Those hints are useful for client UX, but they are not guarantees of runtime behavior. MCP Surface turns common manifest mistakes and risky metadata combinations into deterministic, reviewable CI findings.

## Why this exists

MCP servers are increasingly used as building blocks for agentic workflows. A broken schema, duplicate tool name, missing description, or contradictory annotation can make a tool harder to discover or cause clients to make poor preflight decisions. The current MCP specification also moved tool schemas to full JSON Schema 2020-12, increasing the surface area worth validating.

MCP Surface is intentionally **offline, deterministic, dependency-free at runtime, and CI-friendly**. It does not connect to an MCP server and it does not execute tools.

## Quick start

```bash
python -m mcpsurface.cli tools.json
```

Fail on warnings as well:

```bash
python -m mcpsurface.cli tools.json --fail-on warning
```

Machine-readable output:

```bash
python -m mcpsurface.cli tools.json --format json
```

## Input

The CLI accepts either a JSON object containing a `tools` array or a JSON array of tool objects. Example:

```json
{
  "tools": [
    {
      "name": "search",
      "description": "Search the local catalog",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"}
        },
        "required": ["query"]
      },
      "annotations": {
        "readOnlyHint": true,
        "openWorldHint": false
      }
    }
  ]
}
```

## Rules

| Rule | Severity | Meaning |
|---|---|---|
| MCP001 | warning | No tools are present |
| MCP002 | error | Tool name is missing |
| MCP003 | error | Tool names are duplicated |
| MCP004 | warning | Description is missing |
| MCP005 | error | `inputSchema` is missing or invalid |
| MCP006 | error | `inputSchema` root is not an object |
| MCP007 | error | `annotations` is not an object |
| MCP008 | error | `readOnlyHint=true` conflicts with `destructiveHint=true` |
| MCP009 | warning | Tool is marked potentially destructive |
| MCP010 | info | Tool is marked open-world |

The analyzer deliberately reports annotation issues as **risk signals**, not proof of behavior. Treat MCP annotations as untrusted metadata rather than security guarantees.

## CI

Because the command returns a non-zero exit code at the selected severity threshold, it can be placed directly in a pull-request workflow:

```yaml
- run: python -m mcpsurface.cli tools.json --fail-on error
```

## Scope / non-goals

MCP Surface is a static manifest linter. It does **not**:

- connect to MCP servers;
- execute tools;
- claim that annotations accurately describe implementation behavior;
- replace protocol conformance testing;
- replace schema fuzzing or end-to-end contract tests.

Those boundaries are intentional: a small deterministic check is easier to audit and safe to run on every pull request.

## Development

```bash
python -m pytest
```

The test suite covers duplicate names, missing/invalid schemas, annotation contradictions, and a clean manifest. Runtime dependencies are empty.

## Security

MCP Surface only parses JSON and produces findings. It does not execute manifest-provided commands, make network requests, or import code referenced by a manifest.

## License

MIT
