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

### Method 1: Embedded Token in Remote URL (Not Recommended)

```bash
git remote add origin https://TOKEN@github.com/goprosper/REPO_NAME.git
```

**Example:**
```bash
git remote add origin https://YOUR_TOKEN@github.com/goprosper/ProsperModelsDB.git
git push -u origin main
```

**Security Note:** The token is visible in `.git/config`. To remove it:
```bash
git remote set-url origin https://github.com/goprosper/ProsperModelsDB.git
```

### Method 2: Git Credential Manager (Recommended - Current Setup)

1. Install Git Credential Manager (usually comes with Git for Windows)
2. Configure Git to use credential manager:
   ```bash
   git config --global credential.helper manager-core
   git config --global credential.https://github.com.username goprosper
   ```
3. Set remote without token:
   ```bash
   git remote add origin https://github.com/goprosper/REPO_NAME.git
   ```
4. On first push, Git will prompt for credentials:
   - Username: `goprosper`
   - Password: Use your personal access token
5. Credentials are stored securely in Windows Credential Manager and reused automatically

### Method 3: SSH Keys (Most Secure)

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

### Initial Setup
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://TOKEN@github.com/goprosper/REPO_NAME.git
git push -u origin main
```

### Subsequent Pushes
```bash
git add .
git commit -m "Your commit message"
git push
```

### Check Remote Configuration
```bash
git remote -v
```

### Update Remote URL
```bash
git remote set-url origin NEW_URL
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

### Token Expired
1. Generate new token at https://github.com/settings/tokens
2. Update `~/.kiro/settings/mcp.json`
3. Update git remote URL if using embedded token method
4. Restart Kiro

## Security Best Practices

1. **Never commit tokens to repositories** - They're in `.gitignore` but be careful
2. **Use SSH keys for production** - More secure than tokens
3. **Rotate tokens regularly** - Generate new tokens every 90 days
4. **Use minimal scopes** - Only grant permissions needed
5. **Use Git Credential Manager** - Avoid embedding tokens in remote URLs
