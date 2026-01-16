#!/usr/bin/env python3
"""
Infrastructure Validation Script

This script validates that AWS resources are correctly configured and named
according to our standards, helping prevent issues like API Gateway pointing
to wrong Lambda functions.

Usage:
    python validate-infrastructure.py --environment prod
    python validate-infrastructure.py --all-environments
"""

import boto3
import json
import sys
import argparse
from typing import Dict, List, Optional
from botocore.exceptions import ClientError


class InfrastructureValidator:
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.apigateway_client = boto3.client('apigateway', region_name=region)
        self.apigatewayv2_client = boto3.client('apigatewayv2', region_name=region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=region)
        
    def validate_environment(self, environment: str) -> Dict[str, List[str]]:
        """Validate all resources for a specific environment."""
        issues = {
            'critical': [],
            'warnings': [],
            'info': []
        }
        
        print(f"\n🔍 Validating {environment} environment...")
        
        # Validate Lambda functions
        lambda_issues = self._validate_lambda_functions(environment)
        issues['critical'].extend(lambda_issues.get('critical', []))
        issues['warnings'].extend(lambda_issues.get('warnings', []))
        issues['info'].extend(lambda_issues.get('info', []))
        
        # Validate API Gateways
        api_issues = self._validate_api_gateways(environment)
        issues['critical'].extend(api_issues.get('critical', []))
        issues['warnings'].extend(api_issues.get('warnings', []))
        issues['info'].extend(api_issues.get('info', []))
        
        # Validate DynamoDB tables
        db_issues = self._validate_dynamodb_tables(environment)
        issues['critical'].extend(db_issues.get('critical', []))
        issues['warnings'].extend(db_issues.get('warnings', []))
        issues['info'].extend(db_issues.get('info', []))
        
        return issues
    
    def _validate_lambda_functions(self, environment: str) -> Dict[str, List[str]]:
        """Validate Lambda function naming and configuration."""
        issues = {'critical': [], 'warnings': [], 'info': []}
        
        try:
            # Get all Lambda functions
            paginator = self.lambda_client.get_paginator('list_functions')
            functions = []
            for page in paginator.paginate():
                functions.extend(page['Functions'])
            
            # Filter for prosper-models related functions
            prosper_functions = [
                f for f in functions 
                if 'prosper' in f['FunctionName'].lower() or 
                   'model' in f['FunctionName'].lower()
            ]
            
            expected_pattern = f"prosper-models-{environment}-"
            sam_pattern = f"ProsperModelsDB-{environment}-"
            
            for func in prosper_functions:
                name = func['FunctionName']
                
                # Check naming convention
                if not (name.startswith(expected_pattern) or name.startswith(sam_pattern)):
                    if environment in name:
                        issues['warnings'].append(
                            f"Lambda function '{name}' doesn't follow naming convention. "
                            f"Expected: {expected_pattern}* or {sam_pattern}*"
                        )
                    else:
                        issues['info'].append(
                            f"Lambda function '{name}' may belong to different environment"
                        )
                else:
                    issues['info'].append(f"✅ Lambda function '{name}' follows naming convention")
                
                # Check environment variables
                try:
                    config = self.lambda_client.get_function_configuration(FunctionName=name)
                    env_vars = config.get('Environment', {}).get('Variables', {})
                    
                    if 'TABLE_NAME' in env_vars:
                        table_name = env_vars['TABLE_NAME']
                        if environment not in table_name:
                            issues['critical'].append(
                                f"Lambda '{name}' TABLE_NAME '{table_name}' doesn't match environment '{environment}'"
                            )
                        else:
                            issues['info'].append(f"✅ Lambda '{name}' has correct TABLE_NAME")
                    
                except ClientError as e:
                    issues['warnings'].append(f"Could not check config for Lambda '{name}': {e}")
            
            # Check for duplicate functions
            function_purposes = {}
            for func in prosper_functions:
                name = func['FunctionName']
                # Extract purpose (last part after environment)
                if f"-{environment}-" in name:
                    purpose = name.split(f"-{environment}-", 1)[1]
                    if purpose in function_purposes:
                        issues['critical'].append(
                            f"Duplicate Lambda functions for purpose '{purpose}': "
                            f"{function_purposes[purpose]} and {name}"
                        )
                    else:
                        function_purposes[purpose] = name
            
        except ClientError as e:
            issues['critical'].append(f"Failed to list Lambda functions: {e}")
        
        return issues
    
    def _validate_api_gateways(self, environment: str) -> Dict[str, List[str]]:
        """Validate API Gateway configuration and Lambda integrations."""
        issues = {'critical': [], 'warnings': [], 'info': []}
        
        try:
            # Check REST APIs
            rest_apis = self.apigateway_client.get_rest_apis()['items']
            prosper_rest_apis = [
                api for api in rest_apis 
                if 'prosper' in api['name'].lower() or 'model' in api['name'].lower()
            ]
            
            for api in prosper_rest_apis:
                name = api['name']
                expected_name = f"prosper-models-{environment}-api"
                
                if name != expected_name and environment in name:
                    issues['warnings'].append(
                        f"REST API '{name}' doesn't follow naming convention. Expected: {expected_name}"
                    )
                elif environment not in name:
                    issues['info'].append(f"REST API '{name}' may belong to different environment")
                else:
                    issues['info'].append(f"✅ REST API '{name}' follows naming convention")
                
                # Check Lambda integrations
                self._check_api_lambda_integrations(api['id'], name, environment, issues, 'rest')
            
            # Check HTTP APIs (API Gateway v2)
            http_apis = self.apigatewayv2_client.get_apis()['Items']
            prosper_http_apis = [
                api for api in http_apis 
                if 'prosper' in api['Name'].lower() or 'model' in api['Name'].lower()
            ]
            
            for api in prosper_http_apis:
                name = api['Name']
                expected_name = f"prosper-models-{environment}-api"
                
                if name != expected_name and environment in name:
                    issues['warnings'].append(
                        f"HTTP API '{name}' doesn't follow naming convention. Expected: {expected_name}"
                    )
                elif environment not in name:
                    issues['info'].append(f"HTTP API '{name}' may belong to different environment")
                else:
                    issues['info'].append(f"✅ HTTP API '{name}' follows naming convention")
                
                # Check Lambda integrations
                self._check_api_lambda_integrations(api['ApiId'], name, environment, issues, 'http')
            
        except ClientError as e:
            issues['critical'].append(f"Failed to list API Gateways: {e}")
        
        return issues
    
    def _check_api_lambda_integrations(self, api_id: str, api_name: str, environment: str, 
                                     issues: Dict[str, List[str]], api_type: str):
        """Check if API Gateway integrations point to correct Lambda functions."""
        try:
            if api_type == 'rest':
                # Get resources and methods for REST API
                resources = self.apigateway_client.get_resources(restApiId=api_id)['items']
                for resource in resources:
                    if 'resourceMethods' in resource:
                        for method in resource['resourceMethods']:
                            try:
                                method_info = self.apigateway_client.get_method(
                                    restApiId=api_id,
                                    resourceId=resource['id'],
                                    httpMethod=method
                                )
                                integration = method_info.get('methodIntegration', {})
                                if integration.get('type') == 'AWS_PROXY':
                                    uri = integration.get('uri', '')
                                    if 'lambda' in uri:
                                        # Extract function name from URI
                                        function_name = self._extract_function_name_from_uri(uri)
                                        if function_name:
                                            self._validate_lambda_integration(
                                                function_name, api_name, environment, issues
                                            )
                            except ClientError:
                                continue  # Skip methods we can't access
            
            elif api_type == 'http':
                # Get integrations for HTTP API
                integrations = self.apigatewayv2_client.get_integrations(ApiId=api_id)['Items']
                for integration in integrations:
                    if integration.get('IntegrationType') == 'AWS_PROXY':
                        uri = integration.get('IntegrationUri', '')
                        if 'lambda' in uri:
                            function_name = self._extract_function_name_from_uri(uri)
                            if function_name:
                                self._validate_lambda_integration(
                                    function_name, api_name, environment, issues
                                )
        
        except ClientError as e:
            issues['warnings'].append(f"Could not check integrations for API '{api_name}': {e}")
    
    def _extract_function_name_from_uri(self, uri: str) -> Optional[str]:
        """Extract Lambda function name from integration URI."""
        # URI format: arn:aws:apigateway:region:lambda:path/2015-03-31/functions/arn:aws:lambda:region:account:function:function-name/invocations
        if '/functions/' in uri and '/invocations' in uri:
            function_arn = uri.split('/functions/')[1].split('/invocations')[0]
            if ':function:' in function_arn:
                return function_arn.split(':function:')[1]
        return None
    
    def _validate_lambda_integration(self, function_name: str, api_name: str, 
                                   environment: str, issues: Dict[str, List[str]]):
        """Validate that API Gateway points to correct Lambda function."""
        expected_patterns = [
            f"prosper-models-{environment}-",
            f"ProsperModelsDB-{environment}-"
        ]
        
        if not any(function_name.startswith(pattern) for pattern in expected_patterns):
            if environment in function_name:
                issues['warnings'].append(
                    f"API '{api_name}' integrates with Lambda '{function_name}' "
                    f"which doesn't follow naming convention"
                )
            else:
                issues['critical'].append(
                    f"API '{api_name}' integrates with Lambda '{function_name}' "
                    f"which appears to be from different environment (expected: {environment})"
                )
        else:
            issues['info'].append(
                f"✅ API '{api_name}' correctly integrates with Lambda '{function_name}'"
            )
    
    def _validate_dynamodb_tables(self, environment: str) -> Dict[str, List[str]]:
        """Validate DynamoDB table naming and configuration."""
        issues = {'critical': [], 'warnings': [], 'info': []}
        
        try:
            # Get all tables
            paginator = self.dynamodb_client.get_paginator('list_tables')
            tables = []
            for page in paginator.paginate():
                tables.extend(page['TableNames'])
            
            # Filter for prosper-models related tables
            prosper_tables = [
                table for table in tables 
                if 'prosper' in table.lower() or 'model' in table.lower()
            ]
            
            expected_pattern = f"prosper-models-{environment}-"
            
            for table in prosper_tables:
                if not table.startswith(expected_pattern):
                    if environment in table:
                        issues['warnings'].append(
                            f"DynamoDB table '{table}' doesn't follow naming convention. "
                            f"Expected: {expected_pattern}*"
                        )
                    else:
                        issues['info'].append(
                            f"DynamoDB table '{table}' may belong to different environment"
                        )
                else:
                    issues['info'].append(f"✅ DynamoDB table '{table}' follows naming convention")
        
        except ClientError as e:
            issues['critical'].append(f"Failed to list DynamoDB tables: {e}")
        
        return issues
    
    def print_results(self, issues: Dict[str, List[str]], environment: str):
        """Print validation results in a readable format."""
        print(f"\n📊 Validation Results for {environment} environment:")
        print("=" * 60)
        
        if issues['critical']:
            print(f"\n🚨 CRITICAL ISSUES ({len(issues['critical'])}):")
            for issue in issues['critical']:
                print(f"  ❌ {issue}")
        
        if issues['warnings']:
            print(f"\n⚠️  WARNINGS ({len(issues['warnings'])}):")
            for warning in issues['warnings']:
                print(f"  ⚠️  {warning}")
        
        if issues['info']:
            print(f"\n✅ INFO ({len(issues['info'])}):")
            for info in issues['info']:
                print(f"  ℹ️  {info}")
        
        # Summary
        total_issues = len(issues['critical']) + len(issues['warnings'])
        if total_issues == 0:
            print(f"\n🎉 No issues found in {environment} environment!")
        else:
            print(f"\n📈 Summary: {len(issues['critical'])} critical, {len(issues['warnings'])} warnings")
            if issues['critical']:
                print("⚠️  Please address critical issues immediately!")


def main():
    parser = argparse.ArgumentParser(description='Validate AWS infrastructure configuration')
    parser.add_argument('--environment', '-e', 
                       choices=['dev', 'staging', 'prod'],
                       help='Environment to validate')
    parser.add_argument('--all-environments', '-a', 
                       action='store_true',
                       help='Validate all environments')
    parser.add_argument('--region', '-r', 
                       default='us-east-1',
                       help='AWS region (default: us-east-1)')
    
    args = parser.parse_args()
    
    if not args.environment and not args.all_environments:
        parser.error("Must specify either --environment or --all-environments")
    
    validator = InfrastructureValidator(region=args.region)
    
    environments = ['dev', 'staging', 'prod'] if args.all_environments else [args.environment]
    
    all_critical_issues = []
    
    for env in environments:
        issues = validator.validate_environment(env)
        validator.print_results(issues, env)
        all_critical_issues.extend(issues['critical'])
    
    # Exit with error code if critical issues found
    if all_critical_issues:
        print(f"\n💥 Found {len(all_critical_issues)} critical issues across all environments!")
        sys.exit(1)
    else:
        print(f"\n🎉 All validations passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()