#!/bin/bash

# Deployment script for Lambda SageMaker AutoML Wrapper
# This script builds and deploys the Lambda function using SAM

set -e

echo "🚀 Starting deployment of Lambda SageMaker AutoML Wrapper"

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI is not installed. Please install it first:"
    echo "   https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "template.yaml" ]; then
    echo "❌ template.yaml not found. Please run this script from the lambda function directory."
    exit 1
fi

# Run basic functionality tests first
echo "🧪 Running basic functionality tests..."
python test_basic_functionality.py
if [ $? -ne 0 ]; then
    echo "❌ Basic functionality tests failed. Aborting deployment."
    exit 1
fi

echo "✅ All tests passed. Proceeding with deployment..."

# Build the SAM application
echo "🔨 Building SAM application..."
sam build

if [ $? -ne 0 ]; then
    echo "❌ SAM build failed"
    exit 1
fi

echo "✅ Build successful"

# Check if this is the first deployment
if [ ! -f "samconfig.toml" ]; then
    echo "📝 First deployment detected. Running guided deployment..."
    sam deploy --guided
else
    echo "🚀 Deploying with existing configuration..."
    sam deploy
fi

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed"
    exit 1
fi

echo "✅ Deployment successful!"

# Get the deployed function ARN
echo "📋 Getting deployment information..."
STACK_NAME=$(grep stack_name samconfig.toml | cut -d'"' -f2)
FUNCTION_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].Outputs[?OutputKey==`SageMakerAutoMLWrapperFunctionArn`].OutputValue' --output text)

echo ""
echo "🎉 Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Deployment Information:"
echo "   Stack Name: $STACK_NAME"
echo "   Function ARN: $FUNCTION_ARN"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update your Step Functions workflow to use this Lambda function"
echo "   2. See step-functions-integration-guide.md for detailed instructions"
echo "   3. Test the integration with your existing workflow"
echo ""
echo "💡 Step Functions Integration:"
echo "   Resource: arn:aws:states:::lambda:invoke"
echo "   FunctionName: $FUNCTION_ARN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"