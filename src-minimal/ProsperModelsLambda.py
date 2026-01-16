import os
import json
import base64
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

TABLE_NAME = os.environ.get("TABLE_NAME")
GSI_NAME = os.environ.get("GSI_NAME", "UserIdDateTime")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


# Safely convert Decimal to int/float for JSON
class DecimalJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            # Return int when it's integral, else float
            if o % 1 == 0:
                return int(o)
            return float(o)
        return super().default(o)


def _get_sub_from_event(event):
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


def _ensure_complete_attributes(item):
    """Ensure all required attributes are present in response."""
    required_attrs = [
        "Id", "SubmissionDateTime", "RequestInput", "Status", "ErrorMessage",
        "AutoMLJobName", "SampleSize", "PositiveClassRatio", "ObjectiveMetric",
        "CompletionCriteria", "BestCandidateJobName",
        "BestCandidateTrainingImage", "BestCandidateTrainingInstance",
        "BestCandidateHyperParameters", "BestCandidateMetrics", "JobCost"
    ]

    for attr in required_attrs:
        if attr not in item:
            item[attr] = None

    return item


def _decode_next_key(token):
    if not token:
        return None
    try:
        # URL-safe base64 -> dict
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _encode_next_key(key):
    if not key:
        return None
    raw = json.dumps(key, cls=DecimalJSONEncoder, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def lambda_handler(event, context):
    # Parse inputs
    params = event.get("queryStringParameters") or {}
    limit_default = 20
    try:
        # Support both 'pagesize' (preferred) and 'limit' (fallback) parameters
        pagesize_param = params.get("pagesize")
        limit_param = params.get("limit")

        if pagesize_param:
            try:
                limit = int(pagesize_param)
            except (ValueError, TypeError):
                # If pagesize is invalid, try limit as fallback
                limit = int(limit_param) if limit_param else limit_default
        elif limit_param:
            limit = int(limit_param)
        else:
            limit = limit_default
    except Exception:
        limit = limit_default
    limit = max(1, min(limit, 100))  # clamp 1..100

    next_token = params.get("next")
    exclusive_start_key = _decode_next_key(next_token)

    # Identify user
    user_sub = _get_sub_from_event(event)
    if not user_sub:
        return _response(
            401,
            {"message": "Unauthorized: missing Cognito sub (JWT). "
             "For local testing, send header 'x-user-sub' or ?sub=..."}
        )

    # Build projection of only requested attributes
    # (avoid reserved words with #names)
    expression_attr_names = {
        "#Id": "Id",
        "#SDT": "SubmissionDateTime",
        "#RequestInput": "RequestInput",
        "#Status": "Status",           # 'Status' is a reserved word
        "#ErrorMessage": "ErrorMessage",
        "#AutoMLJobName": "AutoMLJobName",
        "#SampleSize": "SampleSize",
        "#PositiveClassRatio": "PositiveClassRatio",
        "#ObjectiveMetric": "ObjectiveMetric",
        "#CompletionCriteria": "CompletionCriteria",
        "#BestCandidateJobName": "BestCandidateJobName",
        "#BestCandidateTrainingImage": "BestCandidateTrainingImage",
        "#BestCandidateTrainingInstance": "BestCandidateTrainingInstance",
        "#BestCandidateHyperParameters": "BestCandidateHyperParameters",
        "#BestCandidateMetrics": "BestCandidateMetrics",
        "#JobCost": "JobCost"
    }
    projection = ",".join(expression_attr_names.keys())

    # Query the GSI for items of this user, newest first
    try:
        kwargs = {
            "IndexName": GSI_NAME,
            "KeyConditionExpression": Key("UserId").eq(user_sub),
            "ScanIndexForward": False,  # descending on sort key
            "Limit": limit,
            "ProjectionExpression": projection,
            "ExpressionAttributeNames": expression_attr_names,
        }
        if exclusive_start_key:
            kwargs["ExclusiveStartKey"] = exclusive_start_key

        resp = table.query(**kwargs)

        items = resp.get("Items", [])
        # Ensure all items have complete attribute sets
        items = [_ensure_complete_attributes(item) for item in items]
        lek = resp.get("LastEvaluatedKey")
        next_out = _encode_next_key(lek)

        return _response(200, {
            "items": items,
            "next": next_out,
        })
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ValidationException':
            return _response(500, {
                "message": "Invalid attribute projection in DynamoDB query."
            })
        elif error_code in ['ProvisionedThroughputExceededException',
                            'ThrottlingException']:
            return _response(
                503,
                {"message": "Service temporarily unavailable due to load."}
            )
        else:
            return _response(
                500,
                {"message": "Database error occurred while querying."}
            )
    except Exception:
        return _response(
            500,
            {"message": "Internal server error while querying DynamoDB."}
        )


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, cls=DecimalJSONEncoder),
    }