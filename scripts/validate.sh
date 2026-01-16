#!/bin/bash

# Infrastructure Validation Script
# Usage: ./scripts/validate.sh [environment]
# Example: ./scripts/validate.sh prod

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATE_SCRIPT="$SCRIPT_DIR/validate-infrastructure.py"

# Check if Python script exists
if [ ! -f "$VALIDATE_SCRIPT" ]; then
    echo "❌ Validation script not found: $VALIDATE_SCRIPT"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if boto3 is available
if ! python3 -c "import boto3" 2>/dev/null; then
    echo "❌ boto3 is required. Install with: pip install boto3"
    exit 1
fi

# Run validation
if [ $# -eq 0 ]; then
    echo "🔍 Validating all environments..."
    python3 "$VALIDATE_SCRIPT" --all-environments
elif [ "$1" = "all" ]; then
    echo "🔍 Validating all environments..."
    python3 "$VALIDATE_SCRIPT" --all-environments
else
    echo "🔍 Validating $1 environment..."
    python3 "$VALIDATE_SCRIPT" --environment "$1"
fi

echo "✅ Validation complete!"