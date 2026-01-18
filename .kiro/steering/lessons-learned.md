---
inclusion: manual
---

# Lessons Learned

This document captures important lessons and solutions for specific situations encountered during development.

**Usage**: Reference this document manually using `#lessons-learned` in chat when you encounter similar situations.

---

## Git & GitHub

### GitHub Push Protection Blocking Commits
**Situation**: Pushing commits that contain tokens or secrets in files

**Lesson**: GitHub's push protection will block commits containing tokens, even in documentation files.

**Solution**:
- Always use placeholders like `YOUR_TOKEN_HERE` or `[TOKEN]` in documentation
- Never commit actual tokens, even in steering documents
- If blocked, amend the commit to replace tokens with placeholders before pushing

**Example**:
```bash
# Fix the file to use placeholders
git add file.md
git commit --amend -m "Updated message"
git push
```

### Never Create GitHub Actions Workflows Without Permission
**Situation**: AI assistant creates automated GitHub Actions workflows (CI/CD, validation, testing, etc.) without being asked

**Lesson**: Automated GitHub Actions workflows consume GitHub Actions minutes, can fail due to missing secrets/permissions, and may run unexpectedly (scheduled jobs, on every push, etc.). Users should explicitly request CI/CD automation.

**Solution**:
- NEVER create `.github/workflows/*.yml` files unless the user explicitly asks for CI/CD, automation, or GitHub Actions
- If suggesting automation, ask the user first before creating workflow files
- If a workflow already exists and is causing issues, help disable or delete it when requested

**Example**:
```bash
# To disable a workflow, delete the file
git rm .github/workflows/infrastructure-validation.yml
git commit -m "Disable infrastructure validation workflow"
git push
```

---

## MCP Server Configuration

### Wrong Package Manager for MCP Servers
**Situation**: MCP server won't connect, showing package not found errors

**Lesson**: MCP servers can be Node.js packages (use `npx`) or Python packages (use `uvx`). Using the wrong package manager causes connection failures.

**Solution**:
- For Node.js MCP servers: Use `npx` with package name like `@modelcontextprotocol/server-github`
- For Python MCP servers: Use `uvx` with package name
- Check MCP server documentation to determine which runtime it uses

**Example**:
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",  // Node.js package
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

---

## AWS SAM & Lambda

### [Add lessons as you encounter them]

---

## DynamoDB

### [Add lessons as you encounter them]

---

## Step Functions

### [Add lessons as you encounter them]

---

## General Development

### [Add lessons as you encounter them]

---

## Template for New Lessons

When adding a new lesson, use this format:

### [Descriptive Title]
**Situation**: [When does this occur?]

**Lesson**: [What did you learn?]

**Solution**: [How to handle it?]

**Example** (optional):
```
[Code or command examples]
```

