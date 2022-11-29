import json
import boto3
import os
from boto3.session import Session
# from slack_sdk import WebClient
import base64
import logging
import json
import uuid
from datetime import datetime
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ses_client = boto3.client('ses')
lambda_client = boto3.client('lambda')
from boto3.dynamodb.conditions import Key, Attr


PRIMARY_REGION = os.getenv('PRIMARY_REGION') # None
SECONDARY_REGION = os.getenv('SECONDARY_REGION') # None
SEND_EMAIL_FUNCTION = os.getenv('SEND_EMAIL_FUNCTION') # None
SECRET_NAME=os.getenv('SECRET_NAME')

primaryClient = boto3.client('elbv2', region_name= PRIMARY_REGION)
secondaryClient = boto3.client('elbv2', region_name= SECONDARY_REGION)


# ListofARNs= [
#       {
#         "primaryARN": "arn:aws:elasticloadbalancing:us-west-2:489994096722:loadbalancer/app/primary-ALB2-test-ALB/34dbdf70ce9c5b8c",
#         "secondaryARN": "arn:aws:elasticloadbalancing:us-east-1:489994096722:loadbalancer/app/secondary-ALB2-test-ALB/aee1b62d8ec982d7"
#       },
#       {
#         "primaryARN": "arn:aws:elasticloadbalancing:us-west-2:489994096722:loadbalancer/app/primary-ALB1-test-ALB/f0fcc70f9bb4f36f",
#         "secondaryARN": "arn:aws:elasticloadbalancing:us-east-1:489994096722:loadbalancer/app/secondary-ALB1-test-ALB/adf91443b524cc36"
#       },
#       {
#         "primaryARN": "arn:aws:elasticloadbalancing:us-west-2:489994096722:loadbalancer/app/primary-ALB3-test-ALB/5f8eeb7d7ca7d723",
#         "secondaryARN": "arn:aws:elasticloadbalancing:us-east-1:489994096722:loadbalancer/app/secondary-ALB3-test-ALB/af23cb8717c51287"
#       }
#     ]
primaryEC2client= boto3.client('ec2',region_name=PRIMARY_REGION)
secondaryEC2client= boto3.client('ec2',region_name=SECONDARY_REGION)

acmClient = boto3.client('acm', region_name= PRIMARY_REGION)
acmClientSecondary = boto3.client('acm', region_name= SECONDARY_REGION)

R53TABLENAME=os.environ['R53Table_Name']
# DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

route53table = dynamodb.Table(R53TABLENAME)

def lambda_handler(event, context):
    # TODO implement
    print("event:",event)

    ListofARNs=event["ELB_ARN"]

    

    allDifferenceResult = []
    HTML_EMAIL_CONTENT = ''' '''
    try:
        for obj in ListofARNs:
            # Assuming will get both Primary and secondary ARNs
            if "primaryARN" in obj:
                primaryARN=obj["primaryARN"]
            if "secondaryARN" in obj:
                secondaryARN=obj["secondaryARN"]

            # finding difference in Attributes
            primaryELBAttributes = getELBAttributes(primaryClient, primaryARN)
            secondaryELBAttributes = getELBAttributes(secondaryClient, secondaryARN)
            differentAttributesResult = findDifferenceInAttributes(primaryELBAttributes, secondaryELBAttributes)
    
            # finding difference in listeners
            primaryListeners = getELBListners(primaryClient, primaryARN)
            secondaryListeners = getELBListners(secondaryClient, secondaryARN)
            ELBListenersResult = findDifferenceInListeners(primaryListeners, secondaryListeners)

            # finding difference in Security Group
            DifferenceSecurityGroupList=[]
            PrimaryLBDescribe = getLoadBalancerbyARN(primaryClient,primaryARN)
            PrimarySecurityGroups = getSecurityGroup(primaryEC2client,PrimaryLBDescribe["LoadBalancers"][0]["SecurityGroups"])
            SecondaryLBDescribe = getLoadBalancerbyARN(secondaryClient,secondaryARN)

            SecondarySecurityGroups = getSecurityGroup(secondaryEC2client,SecondaryLBDescribe["LoadBalancers"][0]["SecurityGroups"])

            Primaryprotocol,PrimaryPort,Secondaryprotocol,Secondaryport=getSGRules(PrimarySecurityGroups,SecondarySecurityGroups,ingress=True)

            DiffIngressProtocol,DiffIngressPort=findDiffirenceinSecurityGroups(Primaryprotocol,PrimaryPort,Secondaryprotocol,Secondaryport)
            Primaryprotocol_e,PrimaryPort_e,Secondaryprotocol_e,Secondaryport_e=getSGRules(PrimarySecurityGroups,SecondarySecurityGroups,ingress=False)

            DiffEgressProtocol,DiffEgressPort=findDiffirenceinSecurityGroups(Primaryprotocol_e,PrimaryPort_e,Secondaryprotocol_e,Secondaryport_e)
            # print(DiffIngressProtocol,DiffIngressPort)
            # print(DiffEgressProtocol,DiffEgressPort)
            DifferenceSecurityGroupList.append({"InGressProtocol":DiffIngressProtocol})
            DifferenceSecurityGroupList.append({"InGressPort":DiffIngressPort})
            DifferenceSecurityGroupList.append({"EgressProtocol":DiffEgressProtocol})
            DifferenceSecurityGroupList.append({"EgressPort":DiffEgressPort})
            
            # finding difference in target groups
            loadBalancerType = PrimaryLBDescribe["LoadBalancers"][0]["Type"]
            primaryTargetGroups = getTargetGroup(primaryClient, primaryARN)
            secondaryTargetGroups = getTargetGroup(secondaryClient, secondaryARN)
            differentTargetGroupsList = findDifferenceInTargetGroup(primaryTargetGroups,  secondaryTargetGroups, loadBalancerType)
            #finding difference in certificates
            primaryCertificateList = getCertificates(getELBListners(primaryClient, primaryARN))
            secondaryCertificateList =  getCertificates( getELBListners(secondaryClient, secondaryARN))
            
            primaryCertificateList = getSingleListenerCertificateList(acmClient, primaryCertificateList)
            
            secondaryCertificateList = getSingleListenerCertificateList(acmClientSecondary, secondaryCertificateList)

            certificateDfferenceList = findDifferenceInCertificates(primaryCertificateList, secondaryCertificateList)
            # print("Certificate Difference List : ", certificateDfferenceList)
            '''
            Route 53 Difference
            '''
            route53table = dynamodb.Table(R53TABLENAME)

            PrimaryRecordName = read_RecordName(route53table,PrimaryLBDescribe["LoadBalancers"][0]["DNSName"])
            SecondaryRecordName = read_RecordName(route53table,SecondaryLBDescribe["LoadBalancers"][0]["DNSName"])
            RecordNamedifferenceList=RecordNamedifference(PrimaryRecordName,SecondaryRecordName)

            resultReposne = {
            "attributes": differentAttributesResult,
            "listeners" : ELBListenersResult,
            "targetGroups" : differentTargetGroupsList,
            "SecurityGroups": DifferenceSecurityGroupList,
            "certificates" : certificateDfferenceList,
            "RecordNamedifferenceList":RecordNamedifferenceList
            }

            allDifferenceResult.append({"primaryARN" : primaryARN, "secondaryARN" : secondaryARN, "ELBDifferences": resultReposne })
        logger.info(allDifferenceResult)
        # clear ARN table
        # deletedataonTable(route53table)
        if len(allDifferenceResult) > 0:
            print("Payload Sent ...")
            for item in allDifferenceResult:
                print(len(item))
                now=datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                data={
                    'id': str(uuid.uuid1()),
                    'date': dt_string,
                    'primaryARN': item["primaryARN"],
                    'secondaryARN': item["secondaryARN"],
                    'ELBDifferences': item["ELBDifferences"]
                }
                table.put_item(Item=data)

            # lambda_client.invoke(FunctionName=SEND_EMAIL_FUNCTION, 
            #          InvocationType='Event',
            #          Payload= json.dumps({"ELBList": allDifferenceResult})
            #          )
        else:
            print("No Difference Found, Could Sent Pyaload ...")
            
        return {
            'statusCode': 200,
            'body': allDifferenceResult
        }
    
    except Exception as e:
        print(e)
        # slack_token=getSecret()
        # slackclient = WebClient(token= slack_token)
        # slackclient.chat_postMessage(channel="#py-notify", text="Labmda Error Message:  "+str(e))

        return {
            "statusCode": 500,
             "body":{
                 "isError" : "true",
                 "errorMessage" : str(e)
             }
}

'''
Route 53
'''

def read_RecordName(table,DNS):
    result=[]
    print("DNS:",DNS)
    
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('route_54_data')
    # DNS1=
    DNS=DNS.lower()
    tablescan = table.scan(FilterExpression=Attr("DNS").eq(DNS))
    print("tablescan:",tablescan)
    
    if "Items" in tablescan: 
        result.append(tablescan["Items"])
    else:
        result.append({"DNS":DNS, "RecordName": 'Not Found'})

    print("PrimaryALB_RecordName:",result)
    return result
#####

def RecordNamedifference(PrimaryRecordName, SecondaryRecordName):
   PrimaryRecordNameList=[]
   SecondaryRecordNameList=[]
   DifferenceList=[]
   for item in PrimaryRecordName[0]:
      PrimaryRecordNameList.append(item["RecordName"])
   for item in SecondaryRecordName[0]:
      SecondaryRecordNameList.append(item["RecordName"])
   PrimaryRecordNameList.sort()
   SecondaryRecordNameList.sort()
   # print("\nPrimaryRecordNameList:", PrimaryRecordNameList)
   # print("SecondaryRecordNameList:",SecondaryRecordNameList)
   PrimaryRecordNameList2=[]
   SecondaryRecordNameList2=[]
   # if exist than remove
   for P in PrimaryRecordNameList:
      if P not in SecondaryRecordNameList:
         PrimaryRecordNameList2.append(P)
   for S in SecondaryRecordNameList:
      if S not in PrimaryRecordNameList:
         SecondaryRecordNameList2.append(S)
   # print("\nPrimaryRecordNameList2:", PrimaryRecordNameList2)
   # print("SecondaryRecordNameList2:",SecondaryRecordNameList2)

   if len(PrimaryRecordNameList2) > len(SecondaryRecordNameList2):
      x=len(PrimaryRecordNameList2)
      y=len(SecondaryRecordNameList2)
      for P,S in zip(PrimaryRecordNameList2, SecondaryRecordNameList2):
         DifferenceList.append({"RecordName": {"primary": P, "secondary": S}})
      for i in range(y,x):
         DifferenceList.append({"RecordName": {"primary": PrimaryRecordNameList2[i], "secondary": 'not available'}})

   if len(PrimaryRecordNameList2) < len(SecondaryRecordNameList2):         
      x=len(PrimaryRecordNameList2)
      y=len(SecondaryRecordNameList2)
      for P,S in zip(PrimaryRecordNameList2, SecondaryRecordNameList2):
         DifferenceList.append({"RecordName": {"primary": P, "secondary": S}})
      for i in range(x,y):
         DifferenceList.append({"RecordName": {"primary": 'not available', "secondary": SecondaryRecordNameList2[i]}})
            
   if len(PrimaryRecordNameList2) == len(SecondaryRecordNameList2):
      for P,S in zip(PrimaryRecordNameList2, SecondaryRecordNameList2):
         DifferenceList.append({"RecordName": {"primary": P, "secondary": S}})

      
   print("\nDifferenceList:",DifferenceList)
   return DifferenceList

# def deletedataonTable(table):

#    result = table.scan()

#    for item in result["items"]:
#       key=item["id"]
#       print("Key:",key)
#       table.delete_item(
#                     Key={
#                         'id': key
#                     }
#                 ) 

def getSecret():
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=PRIMARY_REGION )
    get_secret_value_response = client.get_secret_value(
            SecretId=SECRET_NAME )
    if 'SecretString' in  get_secret_value_response:
        secret = get_secret_value_response['SecretString']
        return secret
    else:
        decode_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
        return decode_binary_secret
        
        
def getSecurityGroup(client, Sg_Id):
    response = client.describe_security_groups(
        GroupIds=Sg_Id
    )
    return response
    
def getSGRules(PrimarySG,SecondarySG,ingress):
   PrimaryListProtocol=[]
   PrimaryListPort=[]
   SecondaryListProtocol=[]
   SecondaryListPort=[]
   if ingress == True:
      var_ingress="IpPermissions"
   else:
      var_ingress="IpPermissionsEgress"
   for P in PrimarySG["SecurityGroups"]:
      for S in SecondarySG["SecurityGroups"]:
         for ingress_primary in P[var_ingress]:
            for ingress_secondary in S[var_ingress]:
                  if ingress_primary['IpProtocol'] not in PrimaryListProtocol:
                     PrimaryListProtocol.append(ingress_primary['IpProtocol'])
                  if 'FromPort' in ingress_primary:
                     if ingress_primary['FromPort'] not in PrimaryListPort:
                        PrimaryListPort.append(ingress_primary['FromPort'])
                  else:
                     if 0 not in PrimaryListPort:
                        PrimaryListPort.append(0)
                  if ingress_secondary['IpProtocol'] not in SecondaryListProtocol:
                     SecondaryListProtocol.append(ingress_secondary['IpProtocol'])
                  if 'FromPort' in ingress_secondary:
                     if ingress_secondary['FromPort'] not in SecondaryListPort:
                        SecondaryListPort.append(ingress_secondary['FromPort'])
                  else:
                     if 0 not in SecondaryListPort:
                        SecondaryListPort.append(0)
   return PrimaryListProtocol,PrimaryListPort,SecondaryListProtocol,SecondaryListPort

      ### Finding Difference:
def findDiffirenceinSecurityGroups(PrimaryListProtocol,PrimaryListPort,SecondaryListProtocol,SecondaryListPort):
   SGProtocolDifference=[]
   SGPortDifference=[]
   for i in PrimaryListProtocol:
      if i not in SecondaryListProtocol:
         SGProtocolDifference.append({"Protocol": {"primary": i, "secondary": 'not available'}})
   for i in SecondaryListProtocol:
      if i not in PrimaryListProtocol:
         SGProtocolDifference.append({"Protocol": {"primary": 'not available', "secondary": i}})

   for i in PrimaryListPort:
      if i not in SecondaryListPort:
         SGPortDifference.append({"Port": {"primary": i, "secondary": 'not available'}})
   for i in SecondaryListPort:
      if i not in PrimaryListPort:
         SGPortDifference.append({"Port": {"primary": 'not available', "secondary": i}})

   return SGProtocolDifference, SGPortDifference
#####    #####

def getTargetGroup(client, arn):
    response = client.describe_target_groups(
    LoadBalancerArn = arn
    )
    return response

def findDifferenceInTargetGroup(primaryTargetGroups, secondaryTargetGroups, loadBalancerType):
    logger.info("Finding Difference in Target Groups :")
    logger.info("Primary Target Groups : " + str(primaryTargetGroups))
    logger.info("Secondary Target Groups : " + str( secondaryTargetGroups))
    logger.info("Load Balancer Type : " +  loadBalancerType);
    primaryTargetGroupsList = primaryTargetGroups["TargetGroups"]
    secondaryTargetGroupsList = secondaryTargetGroups["TargetGroups"]
    differenceTargetGroupsList = []

    for primaryTargetGroup in primaryTargetGroupsList:
        for secondaryTargetGroup in  secondaryTargetGroupsList:
            targetGroupObj = extractTargetGroupInfo(primaryTargetGroup, secondaryTargetGroup, loadBalancerType)
            differenceTargetGroupsList.append(targetGroupObj);
                    
    return differenceTargetGroupsList
    
def extractTargetGroupInfo(primaryTargetGroup, secondaryTargetGroup, loadBalancerType):
    targetGroupObj = {}
    if primaryTargetGroup["Port"] != secondaryTargetGroup["Port"]:
        targetGroupObj["Port"] =  {"primary" : primaryTargetGroup["Port"], "secondary" : secondaryTargetGroup["Port"] }
    if primaryTargetGroup["Protocol"] != secondaryTargetGroup["Protocol"]:
        targetGroupObj["Protocol"] =  {"primary" : primaryTargetGroup["Protocol"], "secondary" : secondaryTargetGroup["Protocol"] }
        
    if primaryTargetGroup["HealthCheckProtocol"] != secondaryTargetGroup["HealthCheckProtocol"]:
        targetGroupObj["HealthCheckProtocol"] =  {"primary" : primaryTargetGroup["HealthCheckProtocol"], "secondary" : secondaryTargetGroup["HealthCheckProtocol"] }
        
    if primaryTargetGroup["HealthCheckPort"] != secondaryTargetGroup["HealthCheckPort"]:
        targetGroupObj["HealthCheckPort"] =  {"primary" : primaryTargetGroup["HealthCheckPort"], "secondary" : secondaryTargetGroup["HealthCheckPort"] }

    if primaryTargetGroup["HealthCheckEnabled"] != secondaryTargetGroup["HealthCheckEnabled"]:
        targetGroupObj["HealthCheckEnabled"] =  {"primary" : primaryTargetGroup["HealthCheckEnabled"], "secondary" : secondaryTargetGroup["HealthCheckEnabled"] }

    if primaryTargetGroup["HealthCheckIntervalSeconds"] != secondaryTargetGroup["HealthCheckIntervalSeconds"]:
        targetGroupObj["HealthCheckIntervalSeconds"] =  {"primary" : primaryTargetGroup["HealthCheckIntervalSeconds"], "secondary" : secondaryTargetGroup["HealthCheckIntervalSeconds"] }
        
    if primaryTargetGroup["HealthCheckTimeoutSeconds"] != secondaryTargetGroup["HealthCheckTimeoutSeconds"]:
        targetGroupObj["HealthCheckTimeoutSeconds"] =  {"primary" : primaryTargetGroup["HealthCheckTimeoutSeconds"], "secondary" : secondaryTargetGroup["HealthCheckTimeoutSeconds"] }
        
    if primaryTargetGroup["HealthyThresholdCount"] != secondaryTargetGroup["HealthyThresholdCount"]:
        targetGroupObj["HealthyThresholdCount"] =  {"primary" : primaryTargetGroup["HealthyThresholdCount"], "secondary" : secondaryTargetGroup["HealthyThresholdCount"] }
        
        
    if primaryTargetGroup["UnhealthyThresholdCount"] != secondaryTargetGroup["UnhealthyThresholdCount"]:
        targetGroupObj["UnhealthyThresholdCount"] =  {"primary" : primaryTargetGroup["UnhealthyThresholdCount"], "secondary" : secondaryTargetGroup["UnhealthyThresholdCount"] }   

    if loadBalancerType == "application":
       logger.info("Application ALB  : " +  loadBalancerType)
       if primaryTargetGroup["HealthCheckPath"] != secondaryTargetGroup["HealthCheckPath"]:
           targetGroupObj["HealthCheckPath"] =  {"primary" : primaryTargetGroup["HealthCheckPath"], "secondary" : secondaryTargetGroup["HealthCheckPath"] }
        
       if primaryTargetGroup["Matcher"]["HttpCode"] != secondaryTargetGroup["Matcher"]["HttpCode"]:
           targetGroupObj["Matcher"]["HttpCode"] =  {"primary" : primaryTargetGroup["Matcher"]["HttpCode"], "secondary" : secondaryTargetGroup["Matcher"]["HttpCode"] }
    elif loadBalancerType == "network":
        logger.info("Network ALB  : " +  loadBalancerType)
    return targetGroupObj
    
    
# listners
def getELBListners(client, arn):
    response = client.describe_listeners(
    LoadBalancerArn = arn
    )
    return response
    
    

def findDifferenceInListeners(primaryListeners, secondaryListeners):
    logger.info("Finding Difference in Listners : ")
    logger.info("Primary Listeners : " + str(primaryListeners))
    logger.info("Secondary Listeners : " + str(secondaryListeners))
    listenersDifferenceResultList = []
    primaryListenersList = primaryListeners["Listeners"]
    secondaryListenersList = secondaryListeners["Listeners"]
    PrimaryListnerPort=[]
    PrimaryListnerProtocol=[]
    SecondaryListnerPort=[]
    SecondaryListnerProtocol=[]

    for obj in primaryListenersList:
        PrimaryListnerPort.append(obj["Port"])
        PrimaryListnerProtocol.append(obj["Protocol"])

    for obj in secondaryListenersList:
        SecondaryListnerPort.append(obj["Port"])
        SecondaryListnerProtocol.append(obj["Protocol"])
    
    ListnerDifferenceList=[]
    for port in PrimaryListnerPort:
        if port not in SecondaryListnerPort:
            listenersDifferenceResultList.append({"Port": {"primary": port, "secondary": 'not available'}})

    for port in SecondaryListnerPort:
        if port not in PrimaryListnerPort:
            listenersDifferenceResultList.append({"Port": {"primary": "not available", "secondary": port}})

    for protocol in PrimaryListnerProtocol:
        if protocol not in SecondaryListnerProtocol:
            listenersDifferenceResultList.append({"Protocol": {"primary": protocol, "secondary": 'not available'}})

    for protocol in SecondaryListnerProtocol:
        if protocol not in PrimaryListnerProtocol:
            listenersDifferenceResultList.append({"Protocol": {"primary": "not available", "secondary": protocol}})
    
    return listenersDifferenceResultList;
                    

def findDifferenceInCertificates(primaryCertificateList, secondaryCertificateList):

    primary_domain_list = []
    secondary_domain_list = []
    certObj = []
    
    #get all the list of primary and secondary cert domains
    for primaryCertificate in primaryCertificateList:
        primary_domain_list.append(primaryCertificate["Certificate"]["DomainName"])
    for secondaryCertificate in secondaryCertificateList:
        secondary_domain_list.append(secondaryCertificate["Certificate"]["DomainName"])
        
    if len(primaryCertificateList) > 0 and len(secondaryCertificateList) > 0:
        for primary_index in primary_domain_list:
            if primary_index not in secondary_domain_list:
                certObj.append({"domainName" : {"primary" : primary_index, "secondary" : "not available" }})
        for secondary_index in secondary_domain_list:
            if secondary_index not in primary_domain_list:
                certObj.append({"domainName" : {"primary" : "not available", "secondary" : secondary_index }})
                
    elif len(primaryCertificateList) > 0 and len(secondaryCertificateList) == 0:
        for primaryCertificate in primaryCertificateList:
            certObj.append({"domainName" : {"primary" : primaryCertificate["Certificate"]["DomainName"], "secondary" : "None" }})
    elif len(primaryCertificateList) < len(secondaryCertificateList):
        for secondaryCertificate in secondaryCertificateList:
                certObj.append({"domainName" : {"primary" : "None" , "secondary" : secondaryCertificate["Certificate"]["DomainName"] }})

    return certObj;
    
def getCertificates(primaryListeners):
    print("Listener For Certificate   : " , primaryListeners)
    primaryListenersList = primaryListeners["Listeners"]
    # certificate list
    primaryListenerCertificateList = []
    
    for index, primaryListener in  enumerate(primaryListenersList):
        print("Listener Certificate : ", primaryListener)
        if "Certificates" in primaryListener:
            primaryListenerCertificateList.append(primaryListener["Certificates"][0])
            print("Found Certificate ARN : ", primaryListener["Certificates"][0])
    return primaryListenerCertificateList;

def getSingleListenerCertificateList(acmClient, certificateList):
    newList = []
    print("cert arn:",certificateList)
    # print("Function Start")
    for certificate in certificateList:
        newList.append(getCertificateList(acmClient, certificate["CertificateArn"])) # Primary client cert
    # print("Function Ends")
    return newList

def getAllLoadBalancer(client):
    response = client.describe_load_balancers(
    )
    return response
    
def getLoadBalancerbyARN(client,arn):
    response = client.describe_load_balancers(
            LoadBalancerArns=[arn],
    )
    return response
    
def getTagsByArn(client, arn):
    response = client.describe_tags(
    ResourceArns=[
        arn
    ]
    )
    return response
    
def getELBAttributes(client, arn):
    response = client.describe_load_balancer_attributes(
    LoadBalancerArn=arn,
    )
    return response
    
def getCertificateList(acmClient, arn):
    print("cert ARN Single:", arn)
    response = acmClient.describe_certificate(
    CertificateArn=arn
    )
    return response

def fetchDataFromTag(tags):
    logger.info("Fetching Tag : ")
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
    logger.info("Fetching End : ")
    logger.info("The Fetched ARN , Status  and enable are : " + isPrimary +  secondaryARN + enable )
    return isPrimary, secondaryARN, enable
    
def findDifferenceInAttributes(primaryAttributes, secondaryAttributes):
    print("Finding Attributes Difference : ")
    print("Primary Attributes : ", primaryAttributes)
    print("Secondary Attributes : ",  secondaryAttributes)
    primaryAttributesList = primaryAttributes["Attributes"]
    secondaryAttributesList = secondaryAttributes["Attributes"]
    differentAttributesResult = []

    for  primaryAttribute in primaryAttributesList:
        for  secondaryAttribute in secondaryAttributesList:
            if primaryAttribute["Key"] == secondaryAttribute["Key"] and  primaryAttribute["Value"] != secondaryAttribute["Value"]:
                print("Difference In : ", primaryAttribute, secondaryAttribute)
                differentAttributesResult.append({"differentAttribute" : {"primary": primaryAttribute, "secondary": secondaryAttribute}})
                secondaryAttributesList.remove(secondaryAttribute);
    return differentAttributesResult;
