import os
import json
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ.get("TABLE_NAME", "ProsperModels-FeatureLists")

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
    # Preferred: HTTP API JWT authorizer (Cognito) -> requestContext.authorizer.jwt.claims.sub
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

def lambda_handler(event, context):
    # Parse inputs
    params = event.get("queryStringParameters") or {}
    study_name = params.get("StudyName")
    
    if not study_name:
        return _response(
            400,
            {"message": "Missing required parameter: StudyName"}
        )

    # Identify user (for authentication)
    user_sub = _get_sub_from_event(event)
    if not user_sub:
        return _response(
            401,
            {"message": "Unauthorized: missing Cognito sub (JWT). For local testing, send header 'x-user-sub' or ?StudyName=...&sub=..."}
        )

    # Query the table for all FeatureLists for the given StudyName
    try:
        response = table.query(
            KeyConditionExpression=Key("StudyName").eq(study_name),
            ProjectionExpression="FeatureListName"  # Only return the FeatureListName
        )

        items = response.get("Items", [])
        
        # Extract just the FeatureListName values
        feature_list_names = [item["FeatureListName"] for item in items]

        return _response(200, {
            "StudyName": study_name,
            "FeatureListNames": feature_list_names,
            "Count": len(feature_list_names)
        })
        
    except Exception as e:
        # Log detail for troubleshooting
        print(f"ERROR querying DynamoDB: {e}")
        return _response(500, {"message": "Internal server error while querying DynamoDB."})

def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, cls=DecimalJSONEncoder),
    }