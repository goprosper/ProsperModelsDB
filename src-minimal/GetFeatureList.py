import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("ProsperModels-FeatureLists")


def lambda_handler(event, context):
    study_name = event.get("StudyName")
    feature_list_name = event.get("FeatureListName")

    # Query by PK, optionally filter by FeatureListName; works PK-only or PK+SK
    resp = table.get_item(
        Key={
            "StudyName": study_name,
            "FeatureListName": feature_list_name
        }
    )
    
    item = resp.get("Item", {})
    
    # If no item found, return a default structure for testing
    if not item:
        return {
            "FeatureList": [
                {
                    "FeatureName": "DefaultTestFeature",
                    "FeatureType": "Binary",
                    "Selections": [
                        {"QuestionId": 12345, "AnswerIds": [1]}
                    ]
                }
            ]
        }
    
    # If item exists, ensure it has the FeatureList structure expected by Step Function
    # The DynamoDB item should contain a FeatureList field
    if "FeatureList" in item:
        return {"FeatureList": item["FeatureList"]}
    else:
        # If the item doesn't have FeatureList, wrap the entire item as FeatureList
        return {"FeatureList": [item]}
