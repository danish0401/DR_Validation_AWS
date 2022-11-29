import json
import boto3
import os
from boto3.session import Session
import base64
import logging
import uuid
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

route53client = boto3.client('route53')
TABLENAME=os.getenv('TableName')

def lambda_handler(event, context):
    # TODO implement
    
    # DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLENAME)
    
    ## Delete previous Record
    deletedataonTable(table)
    list_hosted_zones = get_all_hosted_zone_id(route53client)
    
    ## Read data from Route53 and store 'DNS','RecordName' in dynamodb table
    
    describe_HostZone(list_hosted_zones, route53client, table)
    
    return {
        'statusCode': 200,
        'body': "Success"
    }

def get_all_hosted_zone_id(route53client):
    
    response = route53client.list_hosted_zones()
    return response

def describe_HostZone(list_hosted_zones, route53client, table):
    for obj in list_hosted_zones["HostedZones"]:
        HostedZoneId = obj["Id"][12:]

        List_resource_Record_Set = route53client.list_resource_record_sets(
            HostedZoneId= HostedZoneId
            )
        put_items(List_resource_Record_Set,table)


def put_items(List_Resource_record_sets,table):
    Data=[]
    for hostedZone in List_Resource_record_sets["ResourceRecordSets"]:
       if "AliasTarget" in hostedZone:
          if "DNSName" in hostedZone["AliasTarget"]: 
             # remove start with dualstack.DNS. also get only elbs
             if hostedZone["AliasTarget"]["DNSName"][0:10:] == "dualstack." and hostedZone["AliasTarget"]["DNSName"][-18:-1:] == "elb.amazonaws.com":
                Data.append({"DNS":hostedZone["AliasTarget"]["DNSName"][10:-1:],"RecordName": hostedZone["Name"][:-1:]})
             elif hostedZone["AliasTarget"]["DNSName"][-18:-1:] == "elb.amazonaws.com":
                Data.append({"DNS":hostedZone["AliasTarget"]["DNSName"][:-1:],"RecordName": hostedZone["Name"][:-1:]})
    for item in Data:
        data={
            'id' : str(uuid.uuid1()),
            'DNS': item["DNS"],
            'RecordName': item["RecordName"]
        }
        table.put_item(Item=data)
    return Data
    
def deletedataonTable(table):
   result = table.scan()
   if "items" in result:
    for item in result["items"]:
        key=item["id"]
        print("Key:",key)
        table.delete_item(
                        Key={
                            'id': key
                        }
                    ) 