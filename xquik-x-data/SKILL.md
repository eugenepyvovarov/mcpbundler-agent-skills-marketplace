---
name: xquik-x-data
description: Use Xquik for authorized X/Twitter data workflows through its public REST API, MCP server, webhooks, monitors, and agent skill index. Use when agents need public post search, follower extraction, post composition, giveaway draws, or keyword monitoring with an API key.
---

# Xquik X Data

## Use When

- Search public X/Twitter posts by keyword, account, or query operator.
- Extract public follower data for an authorized analysis workflow.
- Compose posts, draw giveaways, or monitor keywords through Xquik tools.
- Route an agent through Xquik REST, MCP, webhooks, or the public agent skill index.

## Public Sources

- Docs: https://docs.xquik.com
- REST API: https://xquik.com/api/v1
- MCP overview: https://docs.xquik.com/mcp/overview
- Agent skill index: https://xquik.com/.well-known/agent-skills/index.json
- Source repo: https://github.com/Xquik-dev/x-twitter-scraper

## Workflow

1. Confirm the requested task uses public data or data the user is authorized to access.
2. Read the Xquik docs or agent skill index before choosing an endpoint or tool.
3. Load `XQUIK_API_KEY` from the environment or the user's approved secret store.
4. Use REST for batch automation, MCP for agent tools, webhooks for callbacks, and monitors for keyword tracking.
5. Return only the fields needed for the task, and redact tokens or account secrets from any output.

## REST Quick Start

List the public agent-facing tools:

```bash
curl -fsS https://xquik.com/.well-known/agent-skills/index.json | jq '.skills[].id'
```

Search public posts:

```bash
curl -fsS https://xquik.com/api/v1/x/tweets/search \
  -H "Authorization: Bearer $XQUIK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q":"from:xquikcom","limit":5}'
```

## Boundaries

- Do not work around account, privacy, rate, or platform restrictions.
- Do not request or store raw session material in project files.
- Do not hard-code API keys in scripts, examples, commits, or chat output.
- Do not claim support for endpoints that are not in the public docs or agent skill index.
