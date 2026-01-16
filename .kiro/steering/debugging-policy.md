---
inclusion: always
---

# Debugging and Troubleshooting Policy

## When Debugging or Troubleshooting

When you encounter errors, failures, or unexpected behavior during:
- Code debugging
- Build/deployment failures
- Test failures
- Configuration issues
- Integration problems
- MCP server connection issues
- Git/GitHub operations
- AWS service errors

**You MUST:**

1. **Check the lessons-learned document first** by reading `.kiro/steering/lessons-learned.md`
2. Look for similar situations or error patterns in the lessons learned
3. Apply documented solutions if a matching lesson exists
4. If the situation is new and you find a solution, suggest adding it to lessons-learned

## When to Reference Lessons Learned

**Always check lessons-learned when:**
- Encountering error messages or failures
- Debugging unexpected behavior
- Troubleshooting configuration issues
- Resolving integration problems
- Handling authentication/authorization issues
- Dealing with deployment problems

**The goal**: Learn from past experiences and avoid repeating the same debugging process.

## Adding New Lessons

When you solve a non-trivial problem:
1. Suggest adding it to lessons-learned.md
2. Include: situation, lesson learned, solution, and example
3. Categorize it appropriately (Git, AWS, MCP, etc.)

## Exception

Don't check lessons-learned for:
- Simple syntax errors
- Obvious typos
- Standard feature implementation (not debugging)
- Routine code writing
