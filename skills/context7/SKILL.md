---
name: context7
description: Retrieve current, version-aware library and framework documentation through the Context7 MCP before writing or reviewing code that depends on external APIs.
---

# Context7 Documentation Skill

Use Context7 when a task depends on the current API, configuration, behavior, migration path, or examples for a software library/framework. It is especially useful when stale model knowledge could produce deprecated or invalid code.

## Trigger conditions

Use this skill when:

- implementing code against a named library/framework/package;
- the user asks about a specific library version;
- reviewing code for deprecated APIs;
- upgrading or migrating a dependency;
- an error may be caused by a recently changed API;
- exact current syntax or configuration matters.

Do not use it for language fundamentals or code that does not depend on external library documentation.

## MCP endpoint

Default remote config:

```text
examples/context7.json
```

For higher rate limits, set `CONTEXT7_API_KEY` and use:

```text
examples/context7-auth.json
```

Never commit the API key.

## Required workflow

1. **Resolve the library ID.** Call `resolve-library-id` unless the user already supplied a Context7 ID in `/org/project` or `/org/project/version` form.
2. **Select deliberately.** Prefer exact name/version match, high source reputation, stronger benchmark score, useful snippet coverage, and relevance to the user's task.
3. **Query the docs.** Call `query-docs` with the selected ID and a narrow, specific question.
4. **Split broad questions.** Use separate documentation queries for distinct concepts. Do not use more than 3 `query-docs` calls for one user question.
5. **Use retrieved docs as source of truth** for library-specific API behavior. If the retrieved docs are incomplete or contradictory, say so and fall back to the library's official documentation.
6. **Do not send secrets or proprietary material** in Context7 queries. Never include API keys, passwords, tokens, private customer data, or confidential source code.

## Command examples

Inspect available Context7 tools:

```bash
node src/cli.mjs inspect examples/context7.json
```

Resolve a library:

```bash
node src/cli.mjs call examples/context7.json resolve-library-id \
  '{"libraryName":"Next.js","query":"How do Cache Components work in Next.js 16?"}'
```

Then query the selected library ID:

```bash
node src/cli.mjs call examples/context7.json query-docs \
  '{"libraryId":"/vercel/next.js","query":"How do Cache Components work in Next.js 16?"}'
```

## Agent reasoning policy

Context7 is a documentation retrieval tool, not a substitute for reasoning or testing. The agent should:

```text
user task
  -> identify external dependency
  -> Context7 resolve-library-id
  -> Context7 query-docs
  -> implement/review using retrieved API contract
  -> run relevant tests or verification
```

Prefer one high-quality documentation lookup over repeatedly querying vague terms.
