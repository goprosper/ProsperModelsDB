---
inclusion: always
---

# GitHub Configuration

## Account Information

- **Organization**: goprosper
- **Personal Account**: mperkins55
- **Primary Repository**: https://github.com/goprosper/ProsperModelsDB

## GitHub MCP Server Setup

The GitHub MCP server is configured in `~/.kiro/settings/mcp.json` (user-level config).

### Current Configuration

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_GITHUB_TOKEN_HERE"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Prerequisites

1. **Node.js**: Required for running the GitHub MCP server
   - Check: `node --version`
   - Should be v22.21.0 or higher

2. **npx**: Comes with Node.js
   - Used to run the `@modelcontextprotocol/server-github` package

### Personal Access Token

A personal access token is configured for the **goprosper** account in the MCP configuration file.

**Token Scopes Required:**
- `repo` - Full control of private repositories
- `workflow` - Update GitHub Action workflows (optional)

**To Generate a New Token:**
1. Log into GitHub as `goprosper`
2. Go to: https://github.com/settings/tokens
3. Click "Generate new token" → "Generate new token (classic)"
4. Name: "Kiro MCP Server"
5. Select scopes: `repo`, `workflow`
6. Generate and copy the token
7. Update `~/.kiro/settings/mcp.json` with the new token
8. Restart Kiro or reconnect the MCP server

## Git Authentication for Push/Pull

### Method 1: Git Credential Manager (Recommended - Current Setup)

Git Credential Manager Core securely stores credentials in Windows Credential Manager, eliminating the need to embed tokens in URLs or enter credentials repeatedly.

**Setup Steps:**

1. **Verify Git Credential Manager is installed** (comes with Git for Windows):
   ```bash
   git credential-manager-core --version
   ```

2. **Configure Git to use credential manager**:
   ```bash
   git config --global credential.helper manager-core
   git config --global credential.https://github.com.username goprosper
   ```

3. **Set remote URL without token**:
   ```bash
   git remote add origin https://github.com/goprosper/REPO_NAME.git
   ```
   
   Or update existing remote:
   ```bash
   git remote set-url origin https://github.com/goprosper/REPO_NAME.git
   ```

4. **On first push, Git will prompt for credentials**:
   - Username: `goprosper`
   - Password: Use your personal access token (from MCP config or GitHub settings)

5. **Credentials are stored securely** in Windows Credential Manager and reused automatically for all future operations

**Benefits:**
- Token never visible in `.git/config`
- Credentials encrypted by Windows
- Automatic authentication for all git operations
- Easy to update if token changes

**To view/manage stored credentials:**
- Open Windows Credential Manager: Control Panel → Credential Manager → Windows Credentials
- Look for entries starting with `git:https://github.com`

### Method 2: Embedded Token in Remote URL (Not Recommended)

```bash
git remote add origin https://TOKEN@github.com/goprosper/REPO_NAME.git
```

**Security Warning:** The token is visible in `.git/config` and can be exposed. Use Git Credential Manager instead.

### Method 3: SSH Keys (Most Secure for Production)

1. Generate SSH key for goprosper account:
   ```bash
   ssh-keygen -t ed25519 -C "goprosper@email.com" -f ~/.ssh/id_ed25519_goprosper
   ```

2. Add public key to GitHub:
   - Log into GitHub as `goprosper`
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste contents of `~/.ssh/id_ed25519_goprosper.pub`

3. Configure SSH to use the key:
   - Edit `~/.ssh/config`:
     ```
     Host github.com-goprosper
       HostName github.com
       User git
       IdentityFile ~/.ssh/id_ed25519_goprosper
     ```

4. Use SSH remote URL:
   ```bash
   git remote add origin git@github.com-goprosper:goprosper/ProsperModelsDB.git
   ```

## Common Git Operations

### Initial Setup (with Git Credential Manager)
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/goprosper/REPO_NAME.git
git push -u origin main
# Git will prompt for credentials on first push
# Enter username: goprosper
# Enter password: your_personal_access_token
```

### Subsequent Pushes
```bash
git add .
git commit -m "Your commit message"
git push
# No credentials needed - automatically authenticated
```

### Check Remote Configuration
```bash
git remote -v
# Should show: https://github.com/goprosper/REPO_NAME.git (no token visible)
```

### Update Remote URL
```bash
git remote set-url origin https://github.com/goprosper/REPO_NAME.git
```

### Check Credential Configuration
```bash
git config --global --get credential.helper
# Should show: manager-core

git config --global --get credential.https://github.com.username
# Should show: goprosper
```

## Creating New Repositories

### Via GitHub MCP Server (Kiro)
The AI assistant can create repositories using the GitHub MCP server tools when connected.

### Via GitHub Web Interface
1. Log into https://github.com/goprosper
2. Click "+" → "New repository"
3. Configure settings
4. Create repository
5. Follow the push instructions provided

### Via GitHub CLI
```bash
gh auth login
gh repo create goprosper/REPO_NAME --public --description "Description"
```

## Organization Access

The `goprosper` account is an organization. To manage access:
1. Go to: https://github.com/orgs/goprosper/people
2. Invite members or adjust permissions
3. Members can push to repositories based on their role

## Troubleshooting

### MCP Server Won't Connect
1. Check Node.js is installed: `node --version`
2. Verify token is valid and has correct scopes
3. Check MCP logs in Kiro for error messages
4. Try reconnecting: Command Palette → "MCP: Reconnect Server"

### Push Permission Denied
1. Verify you're using the goprosper token, not mperkins55
2. Check token has `repo` scope
3. Ensure token hasn't expired
4. Verify you have push access to the repository
5. Check stored credentials in Windows Credential Manager

### Token Expired or Needs Update
1. Generate new token at https://github.com/settings/tokens
2. Update `~/.kiro/settings/mcp.json` for MCP server
3. Update stored credentials in Git Credential Manager:
   ```bash
   # Remove old credentials
   git credential-manager-core erase
   # Enter when prompted:
   # protocol=https
   # host=github.com
   # (press Enter twice)
   
   # Next git push will prompt for new credentials
   ```
4. Restart Kiro to reconnect MCP server

### Credentials Not Working
1. Check credential helper is configured:
   ```bash
   git config --global --get credential.helper
   ```
2. Verify username is set to goprosper:
   ```bash
   git config --global --get credential.https://github.com.username
   ```
3. Clear and re-enter credentials using the steps above

## Security Best Practices

1. **Use Git Credential Manager** - Current setup, stores credentials securely
2. **Never commit tokens to repositories** - Use placeholders in documentation
3. **Never embed tokens in remote URLs** - Use clean HTTPS URLs with credential manager
4. **Rotate tokens regularly** - Generate new tokens every 90 days
5. **Use minimal scopes** - Only grant permissions needed (repo, workflow)
6. **Use SSH keys for production** - Most secure option for automated systems
7. **Monitor token usage** - Check GitHub settings for token activity

## Quick Reference

**Current Setup:**
- Organization: `goprosper`
- Repository: `https://github.com/goprosper/ProsperModelsDB`
- Authentication: Git Credential Manager Core
- Remote URL: `https://github.com/goprosper/ProsperModelsDB.git` (no token)
- Credentials stored in: Windows Credential Manager (encrypted)
- MCP Server: GitHub MCP via npx (@modelcontextprotocol/server-github)
