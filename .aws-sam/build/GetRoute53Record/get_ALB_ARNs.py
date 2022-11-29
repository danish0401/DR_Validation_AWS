import json
import boto3
import os
from boto3.session import Session
# from slack_sdk import WebClient
import base64
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ses_client = boto3.client('ses')
lambda_client = boto3.client('lambda')


PRIMARY_REGION = os.getenv('PRIMARY_REGION') # None
SECONDARY_REGION = os.getenv('SECONDARY_REGION') # None
SEND_ARN_BATCH_LIST = os.getenv('SEND_ARN_BATCH_LIST')
CHUNK_SIZE = os.getenv('CHUNK_SIZE')

primaryClient = boto3.client('elbv2', region_name= PRIMARY_REGION)

def lambda_handler(event, context):
    # TODO implement
    
    arn_list = get_primary_secondary_lb_arn()
    # print("arn list", arn_list)
            
    # batch_to_process_one_batch = 2
    chunk_size = int(CHUNK_SIZE)
    # total_batches = len(arn_list) / batch_to_process_one_batch
    
    
    batch_list = get_arn_list_batching(arn_list, chunk_size)
    
    for single_batch in batch_list:
        lambda_client.invoke(FunctionName=SEND_ARN_BATCH_LIST,
                InvocationType = "Event",
                Payload = json.dumps({"ELB_ARN":single_batch}))
    
    
    return {
        'statusCode': 200,
        'body': batch_list
    }


def get_primary_secondary_lb_arn():
    
    arn_list = []
    loadBalancers_response = getAllLoadBalancer(primaryClient)
    
    for arn in loadBalancers_response["LoadBalancers"]:
        # print("P ARN",arn['LoadBalancerArn'])
        primaryARN = arn['LoadBalancerArn']
        tags = getTagsByArn(primaryClient,arn['LoadBalancerArn'])
        isPrimary, secondaryARN, enable = fetchDataFromTag(tags)
        if isPrimary == "true" and enable == "true":
        # print("S ARN",secondaryARN)
            arn_list.append({"primaryARN": primaryARN, "secondaryARN": secondaryARN})
    return arn_list


def get_arn_list_batching(obj, chunk_size):
   chunk_list = list()
   for i in range(0, len(obj), chunk_size):
      chunk_list.append(obj[i:i+chunk_size])
# print(get_arn_batch(data_list))
   return chunk_list

def getAllLoadBalancer(client):
    response = client.describe_load_balancers(
    )
    return response
    
def getTagsByArn(client, arn):
    response = client.describe_tags(
    ResourceArns=[
        arn
    ]
    )
    return response

def fetchDataFromTag(tags):
    # logger.info("Fetching Tag : ")
    isPrimary = ""
    secondaryARN = ""
    enable = ""
    if tags is not None:
        for tagObj in tags["TagDescriptions"]:
            # print(tagObj["Tags"])
            if tagObj["Tags"] is not None:
                for tag in tagObj["Tags"]:
                    if tag["Key"] == "isPrimary" and tag["Value"] == "true" :
                        isPrimary = "true"
                    if tag["Key"] == "secondaryARN" :
                        secondaryARN = tag["Value"]
                    if tag["Key"] == "enable" :
                        enable = tag["Value"]
                        # return tag;
    # logger.info("Fetching End : ")
    # logger.info("The Fetched ARN , Status  and enable are : " + isPrimary +  secondaryARN + enable )
    return isPrimary, secondaryARN, enable