import os
import json
import boto3
from datetime import datetime
from decimal import Decimal

# Environment variables
TABLE_NAME = os.environ.get("TABLE_NAME")

# AWS clients
sagemaker = boto3.client("sagemaker")
pricing = boto3.client("pricing", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

# In-memory cache for pricing data with timestamps
pricing_cache = {}

# Track pricing failures to return 0 for all costs if any API call fails
pricing_failures = []


class DecimalJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 == 0:
                return int(o)
            return float(o)
        return super().default(o)


def _get_sub_from_event(event):
    """Extract user sub from JWT token for Cognito integration."""
    # Preferred: HTTP API JWT authorizer (Cognito) ->
    # requestContext.authorizer.jwt.claims.sub
    try:
        return event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    except Exception:
        pass

    # Fallbacks for local/dev testing only
    # 1) x-user-sub header
    headers = event.get("headers") or {}
    sub = headers.get("x-user-sub")
    if sub:
        return sub

    # 2) ?sub=... query param
    q = event.get("queryStringParameters") or {}
    if q.get("sub"):
        return q["sub"]

    return None


def get_service_suffix(job_type):
    """Get the SageMaker service suffix for a job type."""
    suffix_mapping = {
        'Training': '-Training',
        'Processing': '-Processing',
        'Transform': '-Transform'
    }
    return suffix_mapping.get(job_type, '')


def validate_pricing_data(price_data):
    """Validate pricing data from AWS Pricing API."""
    try:
        if not price_data or not isinstance(price_data, dict):
            return False

        terms = price_data.get('terms', {}).get('OnDemand', {})
        if not terms:
            return False

        # Check if we have at least one term with price dimensions
        for term_key, term_value in terms.items():
            price_dimensions = term_value.get('priceDimensions', {})
            if price_dimensions:
                for price_key, price_value in price_dimensions.items():
                    price_per_unit = price_value.get('pricePerUnit', {})
                    usd_price = price_per_unit.get('USD')
                    if usd_price is not None:
                        try:
                            price_float = float(usd_price)
                            return price_float >= 0
                        except (ValueError, TypeError):
                            continue
        return False
    except Exception:
        return False


def get_instance_pricing(instance_type, job_type):
    """Get hourly pricing for SageMaker instance type using PowerShell script approach."""
    global pricing_failures

    # Use base instance type as cache key (no suffix needed)
    cache_key = instance_type

    # Check cache first (with 24-hour expiration)
    if cache_key in pricing_cache:
        cache_entry = pricing_cache[cache_key]
        if isinstance(cache_entry, dict) and 'timestamp' in cache_entry:
            cache_age = (datetime.utcnow() -
                        cache_entry['timestamp']).total_seconds()
            if cache_age < 86400:  # 24 hours in seconds
                if cache_entry.get('source') == 'api':
                    return cache_entry['rate']
                else:
                    # Cached failure - add to failures list
                    pricing_failures.append(
                        f"Cached pricing failure for {instance_type}")
                    return None
        elif isinstance(cache_entry, (int, float)):
            # Legacy cache entry, treat as API success
            return float(cache_entry)

    try:
        print(f"🔍 Querying pricing for {instance_type} "
              f"(PowerShell approach)")

        # Query by instanceType and location only (like PowerShell script)
        response = pricing.get_products(
            ServiceCode='AmazonSageMaker',
            Filters=[
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'location',
                    'Value': 'US East (N. Virginia)'
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'instanceType',
                    'Value': instance_type
                }
            ],
            MaxResults=100
        )

        if not response['PriceList']:
            error_msg = f"No pricing data found for {instance_type}"
            print(f"❌ {error_msg}")
            pricing_failures.append(error_msg)
            # Cache the failure
            pricing_cache[cache_key] = {
                'rate': None,
                'timestamp': datetime.utcnow(),
                'source': 'failed'
            }
            return None

        # Define acceptable operations for each job type (from PowerShell script)
        operation_mappings = {
            'Training': ['RunInstance', 'Training', 'Train'],
            'Transform': ['RunInstance', 'Transform', 'BatchTransform',
                         'Batch Transform', 'TransformJob'],
            'Processing': ['RunInstance', 'Processing', 'Process']
        }

        acceptable_operations = operation_mappings.get(job_type,
                                                       ['RunInstance'])

        best_rate = None
        best_match_score = -1

        # Process each product and find the best match (like PowerShell script)
        for product_json in response['PriceList']:
            try:
                product = json.loads(product_json)

                if not product.get('product') or not product['product'].get(
                        'attributes'):
                    continue

                attributes = product['product']['attributes']
                operation = attributes.get('operation', '')

                # Score the match (2 = exact operation match, 1 = missing operation,
                # 0 = wrong operation)
                score = 1  # Default for missing operation
                if operation:
                    if operation in acceptable_operations:
                        score = 2  # Exact match
                    else:
                        score = 0  # Wrong operation

                if score == 0:
                    continue  # Skip wrong operations

                # Extract USD on-demand rate
                rate = None
                terms = product.get('terms', {}).get('OnDemand', {})
                if terms:
                    for term_key in terms:
                        term = terms[term_key]
                        price_dimensions = term.get('priceDimensions',
                                                    {})
                        for dim_key in price_dimensions:
                            dimension = price_dimensions[dim_key]
                            price_per_unit = dimension.get('pricePerUnit',
                                                           {})
                            if price_per_unit.get('USD'):
                                rate = float(price_per_unit['USD'])
                                break
                        if rate is not None:
                            break

                if rate is None:
                    continue

                # Keep the best match
                if score > best_match_score:
                    best_match_score = score
                    best_rate = rate
                if best_match_score == 2:  # Perfect match, stop looking
                    break

            except Exception as e:
                print(f"❌ Error processing product: {e}")
                continue

        if best_rate is not None:
            # Cache the successful result
            pricing_cache[cache_key] = {
                'rate': best_rate,
                'timestamp': datetime.utcnow(),
                'source': 'api'
            }

            print(f"✅ Retrieved pricing for {instance_type}: "
                  f"${best_rate}/hour (job type: {job_type})")
            return best_rate
        else:
            error_msg = (f"No valid pricing found for {instance_type} "
                        f"(job type: {job_type})")
            print(f"❌ {error_msg}")
            pricing_failures.append(error_msg)

    except Exception as e:
        error_msg = f"Pricing API error for {instance_type}: {e}"
        print(f"❌ {error_msg}")
        pricing_failures.append(error_msg)

    # Cache the failure
    pricing_cache[cache_key] = {
        'rate': None,
        'timestamp': datetime.utcnow(),
        'source': 'failed'
    }

    return None


def calculate_runtime_hours(start_time, end_time):
    """Calculate runtime in hours between two datetime strings."""
    if not start_time or not end_time:
        return 0.0

    try:
        if isinstance(start_time, str):
            start_dt = datetime.fromisoformat(
                start_time.replace('Z', '+00:00')
            )
        else:
            start_dt = start_time

        if isinstance(end_time, str):
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            end_dt = end_time

        duration = end_dt - start_dt
        return duration.total_seconds() / 3600.0  # Convert to hours
    except Exception as e:
        print(f"Error calculating runtime: {e}")
        return 0.0


def get_training_job_details(job_name):
    """Get details for a training job."""
    try:
        response = sagemaker.describe_training_job(TrainingJobName=job_name)
        return {
            'instance_type': response.get('ResourceConfig', {}).get('InstanceType'),
            'start_time': response.get('TrainingStartTime'),
            'end_time': response.get('TrainingEndTime'),
            'status': response.get('TrainingJobStatus')
        }
    except Exception as e:
        print(f"Error describing training job {job_name}: {e}")
        return None


def get_processing_job_details(job_name):
    """Get details for a processing job."""
    try:
        response = sagemaker.describe_processing_job(
            ProcessingJobName=job_name
        )
        return {
            'instance_type': response.get(
                'ProcessingResources', {}
            ).get('ClusterConfig', {}).get('InstanceType'),
            'start_time': response.get('ProcessingStartTime'),
            'end_time': response.get('ProcessingEndTime'),
            'status': response.get('ProcessingJobStatus')
        }
    except Exception as e:
        print(f"Error describing processing job {job_name}: {e}")
        return None


def get_transform_job_details(job_name):
    """Get details for a transform job."""
    try:
        response = sagemaker.describe_transform_job(
            TransformJobName=job_name
        )
        return {
            'instance_type': response.get(
                'TransformResources', {}
            ).get('InstanceType'),
            'start_time': response.get('TransformStartTime'),
            'end_time': response.get('TransformEndTime'),
            'status': response.get('TransformJobStatus')
        }
    except Exception as e:
        print(f"Error describing transform job {job_name}: {e}")
        return None


def calculate_job_costs(automl_job_name):
    """Calculate costs for all jobs in an AutoML job."""
    global pricing_failures
    pricing_failures = []  # Reset failures list for this calculation

    try:
        # Get list of candidates (underlying jobs)
        response = sagemaker.list_candidates_for_auto_ml_job(
            AutoMLJobName=automl_job_name,
            MaxResults=100  # Adjust if needed
        )

        candidates = response.get('Candidates', [])

        # Initialize cost tracking
        job_costs = {
            'JobTypes': {
                'Training': {
                    'JobCount': 0, 'TotalRuntime': 0.0, 'TotalCost': 0.0
                },
                'Processing': {
                    'JobCount': 0, 'TotalRuntime': 0.0, 'TotalCost': 0.0
                },
                'Transform': {
                    'JobCount': 0, 'TotalRuntime': 0.0, 'TotalCost': 0.0
                }
            },
            'AllJobs': {'JobCount': 0, 'TotalCost': 0.0}
        }

        # Process each candidate
        for candidate in candidates:
            candidate_steps = candidate.get('CandidateSteps', [])

            for step in candidate_steps:
                step_name = step.get('CandidateStepName', '')
                step_type = step.get('CandidateStepType', '')

                job_details = None
                job_type_key = None

                # Determine job type and get details
                if step_type == 'AWS::SageMaker::TrainingJob':
                    job_details = get_training_job_details(step_name)
                    job_type_key = 'Training'
                elif step_type == 'AWS::SageMaker::ProcessingJob':
                    job_details = get_processing_job_details(step_name)
                    job_type_key = 'Processing'
                elif step_type == 'AWS::SageMaker::TransformJob':
                    job_details = get_transform_job_details(step_name)
                    job_type_key = 'Transform'

                if (job_details and job_type_key and
                        job_details['instance_type']):
                    # Calculate runtime
                    runtime_hours = calculate_runtime_hours(
                        job_details['start_time'],
                        job_details['end_time']
                    )

                    if runtime_hours > 0:
                        # Try to get pricing - returns None if API fails
                        hourly_rate = get_instance_pricing(
                            job_details['instance_type'],
                            job_type_key
                        )

                        if hourly_rate is None:
                            # Pricing API failed - this will cause all costs to be 0
                            print(f"❌ Pricing failed for {job_details['instance_type']} - will return zero costs for all jobs")
                            continue

                        job_cost = round(runtime_hours * hourly_rate, 4)

                        # Update job type totals
                        job_costs['JobTypes'][job_type_key][
                            'JobCount'
                        ] += 1
                        job_costs['JobTypes'][job_type_key][
                            'TotalRuntime'
                        ] += runtime_hours
                        job_costs['JobTypes'][job_type_key][
                            'TotalCost'
                        ] += job_cost

                        # Update overall totals
                        job_costs['AllJobs']['JobCount'] += 1
                        job_costs['AllJobs']['TotalCost'] += job_cost

        # Check if any pricing API calls failed - if so, return zero costs for ALL jobs
        if pricing_failures:
            print(f"❌ PRICING API FAILURES DETECTED "
                  f"({len(pricing_failures)} failures):")
            for failure in pricing_failures:
                print(f"   - {failure}")
            print("❌ Returning zero costs for ALL jobs due to pricing failures")
            
            # Return zero costs for all job types
            job_costs = {
                'JobTypes': {
                    'Training': {
                        'JobCount': 0, 'TotalRuntime': 0.0, 'TotalCost': 0.0
                    },
                    'Processing': {
                        'JobCount': 0, 'TotalRuntime': 0.0, 'TotalCost': 0.0
                    },
                    'Transform': {
                        'JobCount': 0, 'TotalRuntime': 0.0, 'TotalCost': 0.0
                    }
                },
                'AllJobs': {'JobCount': 0, 'TotalCost': 0.0},
                'PricingStatus': 'FAILED',
                'PricingFailures': pricing_failures
            }
        else:
            # All pricing succeeded
            job_costs['PricingStatus'] = 'SUCCESS'
        
        return job_costs

    except Exception as e:
        error_msg = f"Error calculating job costs for {automl_job_name}: {e}"
        print(f"❌ {error_msg}")
        return None


def update_dynamodb_record(record_id, job_costs):
    """Update the DynamoDB record with job cost information."""
    try:
        # Convert job costs to JSON string for DynamoDB storage
        job_costs_json = json.dumps(job_costs, cls=DecimalJSONEncoder)

        table.update_item(
            Key={'Id': record_id},
            UpdateExpression='SET JobCost = :job_cost',
            ExpressionAttributeValues={':job_cost': job_costs_json}
        )
        return True
    except Exception as e:
        print(f"Error updating DynamoDB record {record_id}: {e}")
        return False


def lambda_handler(event, context):
    """Main Lambda handler."""
    try:
        # Extract inputs from event
        automl_job_name = event.get('AutoMLJobName')
        record_id = event.get('Id')

        if not automl_job_name:
            return {
                'statusCode': 400,
                'error': 'AutoMLJobName is required'
            }

        if not record_id:
            return {
                'statusCode': 400,
                'error': 'Id is required'
            }

        print(f"Calculating costs for AutoML job {automl_job_name}")

        # Calculate job costs
        job_costs = calculate_job_costs(automl_job_name)

        if job_costs is None:
            return {
                'statusCode': 500,
                'error': 'Failed to calculate job costs'
            }

        # Check if pricing failed
        if job_costs.get('PricingStatus') == 'FAILED':
            print(f"❌ Cost calculation completed with pricing failures "
                  f"for job {automl_job_name}")
            failure_count = len(job_costs.get('PricingFailures', []))
            print(f"❌ Returning zero costs due to {failure_count} "
                  f"pricing API failures")
        else:
            print(f"✅ Cost calculation completed successfully "
                  f"for job {automl_job_name}")
            total_cost = job_costs.get('AllJobs', {}).get('TotalCost', 0)
            print(f"✅ Total calculated cost: ${total_cost}")

        # Update DynamoDB record
        if update_dynamodb_record(record_id, job_costs):
            return {
                'statusCode': 200,
                'message': 'Job costs calculated and saved successfully',
                'JobCost': job_costs
            }
        else:
            return {
                'statusCode': 500,
                'error': 'Failed to update DynamoDB record'
            }

    except Exception as e:
        print(f"❌ Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'error': 'Internal server error'
        }