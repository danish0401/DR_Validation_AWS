import json
import boto3
import logging
import os
lambda_client = boto3.client('lambda')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ses_client = boto3.client('ses')
SOURCE_EMAIL_ADDRESS = os.getenv('SOURCE_EMAIL_ADDRESS') # None
DESTINATION_EMAIL_ADDRESS = os.getenv('DESTINATION_EMAIL_ADDRESS') # None


ROW = '''   
  <tr align="center" >
    <td bgcolor="#EAF0F6">
       <p style="margin:0 0 12px 0;font-size:12px;line-height:24px;font-family:Arial"> {attribute_name}   </p>
    </td>
    <td >
       <p style="margin:0 0 12px 0;font-size:12px;line-height:24px;font-family:Arial">{primary_value}   </p>
    </td>
    <td >
       <p style="margin:0 0 12px 0;font-size:12px;line-height:24px;font-family:Arial">{secondary_value}  </p>
    </td>
</tr>
'''
def lambda_handler(event, context):
    # TODO implement
    print(type(event))
    print("Source Email Address: ",  SOURCE_EMAIL_ADDRESS)
    print("Destination Email Address: ",  DESTINATION_EMAIL_ADDRESS)
    print("Event : ", event)
   #  differencesList  = event["ELBList"]
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    result=table.scan()
    ## delete rows from table
   #  print(result)
    differencesList = result["Items"]
    HTML_EMAIL_CONTENT = ''' '''
    totalDifferences = 0
    # print(differencesList)
    try:
       print("Started ...") 
       for differenceObject in differencesList:
           print("Object : ", differenceObject)
           print("Attributes : ", differenceObject["ELBDifferences"]["attributes"])
           attributesList = differenceObject["ELBDifferences"]["attributes"]
           listenersList = differenceObject["ELBDifferences"]["listeners"]
           targetGroupsList = differenceObject["ELBDifferences"]["targetGroups"]
           SecurityGroupsProtcolIngress=differenceObject["ELBDifferences"]["SecurityGroups"][0]["InGressProtocol"]
           SecurityGroupsPortIngress=differenceObject["ELBDifferences"]["SecurityGroups"][1]["InGressPort"]
           SecurityGroupsProtcolEgress=differenceObject["ELBDifferences"]["SecurityGroups"][2]["EgressProtocol"]
           SecurityGroupsPortEgress=differenceObject["ELBDifferences"]["SecurityGroups"][3]["EgressPort"]
           DomainNameList=differenceObject["ELBDifferences"]["certificates"]
           RecordNameList=differenceObject["ELBDifferences"]["RecordNamedifferenceList"]
           
           if len(attributesList) > 0 or  len(listenersList) > 0 or len(targetGroupsList) > 0  and targetGroupsList[0]  != "" or len(SecurityGroupsProtcolIngress) > 0 or len(SecurityGroupsPortIngress) > 0 or len(SecurityGroupsProtcolEgress) > 0 or len(SecurityGroupsPortEgress) > 0 or len(DomainNameList) > 0 or len(RecordNameList) > 0:
               singleELBHTML = buildSingleELBHTMLContent(attributesList, listenersList, targetGroupsList, SecurityGroupsProtcolIngress, SecurityGroupsProtcolEgress, SecurityGroupsPortIngress, SecurityGroupsPortEgress, DomainNameList,  RecordNameList, differenceObject["primaryARN"], differenceObject["secondaryARN"] )
               HTML_EMAIL_CONTENT += singleELBHTML
               totalDifferences +=1

               
               
    #   print("HTML : ", HTML_EMAIL_CONTENT)
       print("Total Differences : ", totalDifferences)
       if totalDifferences > 0:
          sendEmail(len(differencesList), HTML_EMAIL_CONTENT)
          deletedataonTable(table,differencesList)
          print("Email Sent ...")
       else:
           print("No Difference Found, Could Not Sent Email ...")
        
       return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
       } 
        
    except Exception as e:
        print(e)
        
def deletedataonTable(table, items):
   for item in items:
      key=item["id"]
      print("Key:",key)
      table.delete_item(
                    Key={
                        'id': key
                    }
                ) 


def buildAttributesHTML(attributesList):
    print("Incomming Attributes List ", attributesList)
    ATTRIBUTES_HTML_CONTENT = ""
    if len(attributesList) == 0:
      updatedRow = ROW.format(attribute_name = "N/A", primary_value= "N/A", secondary_value="N/A")
      ATTRIBUTES_HTML_CONTENT += updatedRow
    else:
      for attribute in attributesList:
         attribute_obj = attribute["differentAttribute"]
         attribute_name = attribute_obj["primary"]["Key"]
         primary_value = attribute_obj["primary"]["Value"]
         secondary_value = attribute_obj["secondary"]["Value"]
         primaryKey = attribute_obj["primary"]["Key"];
         updatedRow = ""
         
         if primaryKey == "deletion_protection.enabled":
               updatedRow = ROW.format(attribute_name = "Deletion Enabled", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "deletion_protection.enabled":
               updatedRow = ROW.format(attribute_name = "Deletion Enabled", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "access_logs.s3.enabled":
               updatedRow = ROW.format(attribute_name = "Access Log", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "access_logs.s3.bucket":
               updatedRow = ROW.format(attribute_name = "Log S3", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "access_logs.s3.prefix":
               updatedRow = ROW.format(attribute_name = "Log S3 Prefix", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "ipv6.deny_all_igw_traffic":
               updatedRow = ROW.format(attribute_name = "IGW Traffic", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "idle_timeout.timeout_seconds":
               updatedRow = ROW.format(attribute_name = "Idle Timeout", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "routing.http.desync_mitigation_mode":
               updatedRow = ROW.format(attribute_name = "Desync mitigation ", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "routing.http.drop_invalid_header_fields.enabled":
               updatedRow = ROW.format(attribute_name = "Drop Invalid Headers", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "routing.http.preserve_host_header.enabled":
               updatedRow = ROW.format(attribute_name = "Host Header", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "routing.http.x_amzn_tls_version_and_cipher_suite.enabled":
               updatedRow = ROW.format(attribute_name = "Headers TLS", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "routing.http.xff_client_port.enabled":
               updatedRow = ROW.format(attribute_name = "X-Forwarded-For Port", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "routing.http.xff_header_processing.mode":
               updatedRow = ROW.format(attribute_name = "X-Forward-For header", primary_value= primary_value, secondary_value=secondary_value)
         
         if primaryKey == "routing.http2.enabled":
               updatedRow = ROW.format(attribute_name = "HTTP/2", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "waf.fail_open.enabled":
               updatedRow = ROW.format(attribute_name = "X-Forward-For header", primary_value= primary_value, secondary_value=secondary_value)
               
         if primaryKey == "load_balancing.cross_zone.enabled":
               updatedRow = ROW.format(attribute_name = "WAF fail open", primary_value= primary_value, secondary_value=secondary_value)
               
         ATTRIBUTES_HTML_CONTENT += updatedRow
    return ATTRIBUTES_HTML_CONTENT
     
         
def buildListenersHTML(listenersList):
    print("Incomming Listner List ", listenersList)
    LISTENERS_HTML_CONTENT = ""
    if len(listenersList) == 0:
      updatedRow = ROW.format(attribute_name = "N/A", primary_value= "N/A", secondary_value="N/A")
      LISTENERS_HTML_CONTENT += updatedRow
    else:  
      for listener in listenersList:
         if "Port" in listener:
               updatedRow = ROW.format(attribute_name = "Port", primary_value= listener["Port"]["primary"], secondary_value=listener["Port"]["secondary"])
               
         if "Protocol" in listener:
               updatedRow = ROW.format(attribute_name = "Protocol", primary_value= listener["Protocol"]["primary"], secondary_value=listener["Protocol"]["secondary"])
               
         LISTENERS_HTML_CONTENT += updatedRow
    return LISTENERS_HTML_CONTENT
    
def buildSGProtocolHTML(ProtocolList, PortList):
    print("Incomming ProtocolList:",ProtocolList)
    INGRESS_HTML_CONTENT = ""
    updatedRow=""
    if len(ProtocolList) == 0 and len(PortList) == 0:
      updatedRow = ROW.format(attribute_name = "N/A", primary_value= "N/A", secondary_value="N/A")
      INGRESS_HTML_CONTENT += updatedRow
    else:
      for obj in ProtocolList:
         if "Protocol" in obj:
               updatedRow = ROW.format(attribute_name = "Protocol", primary_value= obj["Protocol"]["primary"], secondary_value=obj["Protocol"]["secondary"])
         
         INGRESS_HTML_CONTENT+= updatedRow
      for obj in PortList:
         if "Port" in obj:
               updatedRow = ROW.format(attribute_name = "Port", primary_value= obj["Port"]["primary"], secondary_value=obj["Port"]["secondary"])
         
         INGRESS_HTML_CONTENT+= updatedRow      
    return INGRESS_HTML_CONTENT

def buildSGPortHTML(PortList):
    print("Incomming PortList:",PortList)
    updatedRow=""
    INGRESS_HTML_CONTENT = ""
    if len(PortList) == 0:
      updatedRow = ROW.format(attribute_name = "Port", primary_value= "N/A", secondary_value="N/A")
      INGRESS_HTML_CONTENT += updatedRow
    else:
      for obj in PortList:
         if "Port" in obj:
               updatedRow = ROW.format(attribute_name = "Port", primary_value= obj["Port"]["primary"], secondary_value=obj["Port"]["secondary"])
         
         INGRESS_HTML_CONTENT+= updatedRow
    return INGRESS_HTML_CONTENT

def buildDomainName(DomainList):
    print("Incomming DomainList:",DomainList)
    updatedRow=""
    dName_HTML_CONTENT = ""
    if len(DomainList) == 0:
      updatedRow = ROW.format(attribute_name = "N/A", primary_value= "N/A", secondary_value="N/A")
      dName_HTML_CONTENT += updatedRow
    else:
      for obj in DomainList:
         if "domainName" in obj:
               updatedRow = ROW.format(attribute_name = "DomainName", primary_value= obj["domainName"]["primary"], secondary_value=obj["domainName"]["secondary"])
         
         dName_HTML_CONTENT+= updatedRow
    return dName_HTML_CONTENT

def buildRecordName(RecordNameList):
    print("Incomming RecordName:",RecordNameList)
    updatedRow=""
    RName_HTML_CONTENT = ""
    if len(RecordNameList) == 0:
      updatedRow = ROW.format(attribute_name = "N/A", primary_value= "N/A", secondary_value="N/A")
      RName_HTML_CONTENT += updatedRow
    else:
      for obj in RecordNameList:
         if "RecordName" in obj:
               updatedRow = ROW.format(attribute_name = "RecordName", primary_value= obj["RecordName"]["primary"], secondary_value=obj["RecordName"]["secondary"])
         
         RName_HTML_CONTENT+= updatedRow
    return RName_HTML_CONTENT
# def buildCertifcateHTML(certficateObj):
#     print("Incomming Certicate Object ", certficateObj)
#     CERTIFICATE_HTML_CONTENT = ""
#     if "domainName" in certficateObj:
#         updatedRow = ROW.format(attribute_name = "Domain Name", primary_value= certficateObj["domainName"]["primary"], secondary_value=certficateObj["domainName"]["secondary"])
#         CERTIFICATE_HTML_CONTENT += updatedRow
#     return CERTIFICATE_HTML_CONTENT
    
def buildTargetGroupsHTML(targetGroupsList, loadBalancerType="application"):
    print("Incomming Target Group : ",  targetGroupsList)
    TARGET_GROUP_HTML_CONTENT = ""
    if len(targetGroupsList) == 0:
      updatedRow = ROW.format(attribute_name = "N/A", primary_value= "N/A", secondary_value="N/A")
      TARGET_GROUP_HTML_CONTENT += updatedRow
    else:
      for targetGroup in targetGroupsList:
         updatedRow = ""
         print(targetGroup)
         
         if "Port" in targetGroup:
               updatedRow += ROW.format(attribute_name = "Port", primary_value= targetGroup["Port"]["primary"], secondary_value=targetGroup["Port"]["secondary"])
               
         if "Protocol" in targetGroup:
               updatedRow += ROW.format(attribute_name = "Protocol", primary_value= targetGroup["Protocol"]["primary"], secondary_value=targetGroup["Protocol"]["secondary"])
         
         if "HealthCheckPort" in targetGroup:
               updatedRow += ROW.format(attribute_name = "Health Check Port", primary_value= targetGroup["HealthCheckPort"]["primary"], secondary_value=targetGroup["HealthCheckPort"]["secondary"])
         
         if "HealthCheckEnabled" in targetGroup:
               updatedRow += ROW.format(attribute_name = "Health Check Enabled", primary_value= targetGroup["HealthCheckEnabled"]["primary"], secondary_value=targetGroup["HealthCheckEnabled"]["secondary"])
         
         if "HealthCheckIntervalSeconds" in targetGroup:
               updatedRow += ROW.format(attribute_name = "Health Check Interval Seconds", primary_value= targetGroup["HealthCheckIntervalSeconds"]["primary"], secondary_value=targetGroup["HealthCheckIntervalSeconds"]["secondary"])
         
         if "HealthCheckTimeoutSeconds" in targetGroup:
               updatedRow += ROW.format(attribute_name = "Health Check Timeout Seconds", primary_value= targetGroup["HealthCheckTimeoutSeconds"]["primary"], secondary_value=targetGroup["HealthCheckTimeoutSeconds"]["secondary"])
               
         if "HealthyThresholdCount" in targetGroup:
               updatedRow += ROW.format(attribute_name = "Healthy Threshold Count", primary_value= targetGroup["HealthyThresholdCount"]["primary"], secondary_value=targetGroup["HealthyThresholdCount"]["secondary"])
         
         if "UnhealthyThresholdCount" in targetGroup:
               updatedRow += ROW.format(attribute_name = "Unhealthy Threshold Count", primary_value= targetGroup["UnhealthyThresholdCount"]["primary"], secondary_value=targetGroup["UnhealthyThresholdCount"]["secondary"])
         
         if "HealthCheckPath" in targetGroup:
               updatedRow += ROW.format(attribute_name = "Health Check Path", primary_value= targetGroup["HealthCheckPath"]["primary"], secondary_value=targetGroup["HealthCheckPath"]["secondary"])
         
         if "Matcher" in targetGroup:
               updatedRow += ROW.format(attribute_name = "Matcher HttpCode", primary_value= targetGroup["Matcher"]["HttpCode"]["primary"], secondary_value=targetGroup["Matcher"]["HttpCode"]["secondary"])
         
         if "HealthCheckProtocol" in targetGroup:
               updatedRow += ROW.format(attribute_name = "HealthCheckProtocol", primary_value= targetGroup["HealthCheckProtocol"]["primary"], secondary_value=targetGroup["HealthCheckProtocol"]["secondary"])

         TARGET_GROUP_HTML_CONTENT += updatedRow;
    return TARGET_GROUP_HTML_CONTENT;
    
def buildSingleELBHTMLContent(attributesList, listenersList, targetGroupsList, SecurityGroupsProtcolIngress, SecurityGroupsProtcolEgress, SecurityGroupsPortIngress, SecurityGroupsPortEgress, DomainNameList, RecordNameList, primaryELBARN, secondaryELBARN):
    
    ATTRIBUTES_HTML_CONTENT = buildAttributesHTML(attributesList)
    LISTENERS_HTML_CONTENT = buildListenersHTML(listenersList)
    ### Sec Group ###
    INGRESS_HTML_CONTENT_PROTOCOL = buildSGProtocolHTML(SecurityGroupsProtcolIngress, SecurityGroupsPortIngress)
    # INGRESS_HTML_CONTENT_PORT = buildSGPortHTML(SecurityGroupsPortIngress)
    EGRESS_HTML_CONTENT_PROTOCOL=buildSGProtocolHTML(SecurityGroupsProtcolEgress, SecurityGroupsPortEgress)
    # EGRESS_HTML_CONTENT_PORT=buildSGPortHTML(SecurityGroupsPortEgress)
    dNAME_HTML_CONTENT = buildDomainName(DomainNameList)
    RecordNameHTML= buildRecordName(RecordNameList)
    TARGET_GROUPS_HTML_CONTENT = buildTargetGroupsHTML(targetGroupsList)
   
    
    single_elb_html = ''' 
    
     <!-- single start -->
         <table role="presentation" border="0" width="100%">
            <tr align="center">
               <!-- Attributes Differences  -->
               <td style="vertical-align:top;">
                  <table role="presentation" border="0" width="100%" style="margin-left: -5px; margin-bottom: -3px; width: 105%;">
                     <tr>
                        <td bgcolor="#EAF0F6" align="center" style="padding: 15px 15px;">
                           <h2 style="font-size: 15px; margin:0 0 0px 0; font-family:Arial, Helvetica, sans-serif;"> Attributes Differences </h2>
                        </td>
                     </tr>
                  </table>
                  <table role="presentation" border="0" width="100%" cellspacing="0">
                     <tr align="center">
                        <td bgcolor="#EAF0F6">
                           <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Attribute Name</h2>
                        </td>
                        <td >
                           <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Primary ELB</h2>
                        </td>
                        <td >
                           <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Secondary ELB </h2>
                        </td>
                     </tr>
                     {ATTRIBUTES_HTML_CONTENT}
                     <!-- values row -->
                  </table>
               </td>
               <!-- Attributes Differences ends  -->

               <!-- Listeners Differences  -->
               <td style="vertical-align:top;">
                  <table role="presentation" border="0" width="100%" style="margin-left: -5px; margin-bottom: -3px; width: 105%;">
                     <tr>
                        <td bgcolor="#EAF0F6" align="center" style="padding: 15px 15px;">
                           <h2 style="font-size: 15px; margin:0 0 0px 0; font-family:Arial, Helvetica, sans-serif;"> Listeners Differences </h2>
                        </td>
                     </tr>
                  </table>
                  <table role="presentation" border="0" width="100%" cellspacing="0">
                     <tr align="center">
                        <td bgcolor="#EAF0F6">
                           <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Property Name</h2>
                        </td>
                        <td >
                           <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Primary ELB</h2>
                        </td>
                        <td >
                           <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Secondary ELB </h2>
                        </td>
                     </tr>
                     {LISTENERS_HTML_CONTENT}
                     <!-- values row -->
                  </table>
               </td>
               <!-- Listeners Differences  end-->

               <!-- Target Groups Differences -->
               <td style="vertical-align:top;">
                  <table role="presentation" border="0" width="100%" style="margin-left: -5px; margin-bottom: -3px; width: 105%;">
                     <tr>
                        <td bgcolor="#EAF0F6" align="center" style="padding: 15px 15px;">
                           <h2 style="font-size: 15px; margin:0 0 0px 0; font-family:Arial, Helvetica, sans-serif;"> Target Groups Differences </h2>
                        </td>
                     </tr>
                  </table>
                  <table role="presentation" border="0" width="100%" cellspacing="0">
                     <tr align="center">
                        <td bgcolor="#EAF0F6">
                           <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Property Name</h2>
                        </td>
                        <td >
                           <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Primary ELB</h2>
                        </td>
                        <td >
                           <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Secondary ELB </h2>
                        </td>
                     </tr>
                    {TARGET_GROUPS_HTML_CONTENT}
                     <!-- values row -->
                  </table>
               </td>
               <!-- Target Groups Differences end -->
            </tr>
            <!--  -->

         </table>
         
         
         
           <!--second row for security groups differences -->
         <table role="presentation" border="0" width="100%">

          <tr  align="center" >
            <td  style="vertical-align:top; " >
               <table role="presentation" border="0" width="100%" style="margin-left: -5px; margin-bottom: -3px; width: 105%;">
                  <tr>
                     <td bgcolor="#EAF0F6" align="center" style="padding: 15px 15px;">
                        <h2 style="font-size: 15px; margin:0 0 0px 0; font-family:Arial, Helvetica, sans-serif;"> Ingress Security Groups Diff </h2>
                     </td>
                  </tr>
               </table>

               <table role="presentation" border="0" width="100%" cellspacing="0">
                  <tr align="center">
                     <td bgcolor="#EAF0F6">
                        <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Attribute Name</h2>
                     </td>
                     <td >
                        <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Primary Sec Group</h2>
                     </td>
                     <td >
                        <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Secondary Sec Group </h2>
                     </td>
                  </tr>
                 {INGRESS_HTML_CONTENT_PROTOCOL}
                 
                  <!-- values row -->
               </table>
            </td>

            <td  style="vertical-align:top;" >
               <table role="presentation" border="0" width="100%" style="margin-left: -5px; margin-bottom: -3px; width: 105%;">
                  <tr>
                     <td bgcolor="#EAF0F6" align="center" style="padding: 15px 15px;">
                        <h2 style="font-size: 15px; margin:0 0 0px 0; font-family:Arial, Helvetica, sans-serif;"> Egress Security Groups Diff </h2>
                     </td>
                  </tr>
               </table>

               <table role="presentation" border="0" width="100%" cellspacing="0">
                  <tr align="center">
                     <td bgcolor="#EAF0F6">
                        <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Attribute Name</h2>
                     </td>
                     <td >
                        <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Primary Sec Group</h2>
                     </td>
                     <td >
                        <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Secondary Sec Group </h2>
                     </td>
                  </tr>
                 {EGRESS_HTML_CONTENT_PROTOCOL}
                 
               </table>
            </td>
            <td  style="vertical-align:top;" >
               <table role="presentation" border="0" width="100%" style="margin-left: -5px; margin-bottom: -3px; width: 105%;">
                  <tr>
                     <td bgcolor="#EAF0F6" align="center" style="padding: 15px 15px;">
                        <h2 style="font-size: 15px; margin:0 0 0px 0; font-family:Arial, Helvetica, sans-serif;"> ALB Certificate Diff </h2>
                     </td>
                  </tr>
               </table>

               <table role="presentation" border="0" width="100%" cellspacing="0">
                  <tr align="center">
                     <td bgcolor="#EAF0F6">
                        <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Attribute Name</h2>
                     </td>
                     <td >
                        <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Primary Sec Group</h2>
                     </td>
                     <td >
                        <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Secondary Sec Group </h2>
                     </td>
                  </tr>
                    {dNAME_HTML_CONTENT}
                  <!-- values row -->
               </table>
            </td>
            
        </tr>
      </table>
      
      <!-- New Table 3 -->
      <table role="presentation" border="0" width="50%">

         <tr  align="center" >
           <td  style="vertical-align:top; " >
              <table role="presentation" border="0" width="100%" style="margin-left: -5px; margin-bottom: -3px; width: 105%;">
                 <tr>
                    <td bgcolor="#EAF0F6" align="center" style="padding: 15px 15px;">
                       <h2 style="font-size: 15px; margin:0 0 0px 0; font-family:Arial, Helvetica, sans-serif;"> Route53 RecordName Difference </h2>
                    </td>
                 </tr>
              </table>

              <table role="presentation" border="0" width="100%" cellspacing="0">
                 <tr align="center">
                    <td bgcolor="#EAF0F6">
                       <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Attribute Name</h2>
                    </td>
                    <td >
                       <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Primary Route53</h2>
                    </td>
                    <td >
                       <h2 style="font-size: 13px;  font-family:Arial, Helvetica, sans-serif;"> Secondary Route53 </h2>
                    </td>
                 </tr>
                  {RecordNameHTML}
                 <!-- values row -->
              </table>
           </td>


        </tr>
     </table>
      
         
           <table   role="presentation" border="0" width="100%">

            <!-- third row for arns -->
            <tr>
               <td colspan="3">
                  <table role="presentation" border="0" width="100%">
                     <tr>
                    <td bgcolor="#EAF0F6" align="center" style="padding: 15px 15px;">
                           <p style="font-size: 13px; margin:0 0 0px 0; "> <b> Primary ARN:</b> {primaryELBARN} </p>
                        </td>
                     </tr>
                     <tr>
                        <td bgcolor="#EAF0F6" align="center" style="padding: 15px 15px;">
                           <p style="font-size: 13px; margin:0 0 0px 0; "> <b>Secondary ARN:</b> {secondaryELBARN} </p>
                        </td>
                     </tr>
                  </table>
               </td>
            </tr>
            </table>
          <hr>
         <!-- single ends -->
    '''
    html = single_elb_html.format(ATTRIBUTES_HTML_CONTENT=ATTRIBUTES_HTML_CONTENT, LISTENERS_HTML_CONTENT=LISTENERS_HTML_CONTENT, TARGET_GROUPS_HTML_CONTENT=TARGET_GROUPS_HTML_CONTENT,INGRESS_HTML_CONTENT_PROTOCOL=INGRESS_HTML_CONTENT_PROTOCOL, EGRESS_HTML_CONTENT_PROTOCOL=EGRESS_HTML_CONTENT_PROTOCOL, dNAME_HTML_CONTENT=dNAME_HTML_CONTENT, primaryELBARN=primaryELBARN, secondaryELBARN=secondaryELBARN, RecordNameHTML=RecordNameHTML)
    return html

def buildHTML(totalLoadBalancers, DYNAMIC_HTML_CONTENT):
    HTML_EMAIL_CONTENT = ''' 
   <!DOCTYPE html>
   <html lang="en">
   <head>
      <meta charset="UTF-8">
      <meta http-equiv="X-UA-Compatible" content="IE=edge">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Document</title>
   </head>
   <body>
      <div id="email" style="width:1000px;margin: auto;background:white;">
         <!--  Email Title --> 
         <table role="presentation" border="0" width="100%" cellspacing="0">
            <tr>
               <td style="padding: 30px 30px 30px 60px;">
                  <h2 style="font-size: 28px; margin:0 0 20px 0; font-family:Arial, Helvetica, sans-serif;"> Elastic Load Balancer Differences </h2>
                  <p style="margin:0 0 0px 0;font-size:16px;line-height:24px;font-family:Arial"> Below  you can find a list of  load balancers with differences in  Attributes, Listerners and Target Groups .</p>
               </td>
            </tr>
         </table>
        
         {DYNAMIC_HTML_CONTENT}
         <!-- Footer --> 
         <table role="presentation" border="0" width="100%">
            <tr>
               <td bgcolor="#EAF0F6" align="center" style="padding: 30px 30px;">
                  <h2 style="font-size: 20px; margin:0 0 20px 0; font-family:Arial, Helvetica, sans-serif;"> Total Load Balancers : {totalLoadBalancers} </h2>
                  <p style="margin:0 0 12px 0;font-size:16px;line-height:24px;font-family:Arial">These are the number of load balancers tagged with  <br>
                     <code  style="font-size: 13px;">enable : true </code><br> 
                     <code  style="font-size: 13px;">isPrimary : true</code> <br>
                     <code  style="font-size: 13px;">secondaryARN : ARN</code> 
                  </p>
               </td>
            </tr>
         </table>

      </div>
   </body>
</html>
       '''
    updatedContent = HTML_EMAIL_CONTENT.format(DYNAMIC_HTML_CONTENT=DYNAMIC_HTML_CONTENT, totalLoadBalancers=totalLoadBalancers)   
    
    return updatedContent
    
    
def sendEmail(totalLoadBalancers, DYNAMIC_HTML_CONTENT):
    CHARSET = "UTF-8"
    HTML_EMAIL_CONTENT = buildHTML(totalLoadBalancers, DYNAMIC_HTML_CONTENT)
    response = ses_client.send_email(
        Destination={
            "ToAddresses": [
                DESTINATION_EMAIL_ADDRESS,
            ],
        },
        Message={
            "Body": {
                "Html": {
                    "Charset": CHARSET,
                    "Data": HTML_EMAIL_CONTENT,
                }
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": "ELB Differences",
            },
        },
        Source=SOURCE_EMAIL_ADDRESS,
      
    )

