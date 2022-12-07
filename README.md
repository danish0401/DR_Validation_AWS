# SAM Project to find differences between ELBs deployed in primary and secondary Region in aws account

### Project structure:

- handlers: code for all lambda functions
- template.yml: A template defines the application's AWS resources.

```
 sam-app/
   ├── README.md
   ├── handlers/
   │   ├── get_route53_records.py
   │   ├── get_ALB_ARNs.py       
   │   ├── send_email .py
   │   ├── requirements.txt
   │   └── find_elb_difference.py
   └── template.yaml         #Contains the AWS SAM template defining your application's AWS resources.
```
#### Labmda Functions:
This application consist of four lambda functions that has different functionality and depends upon each other.
- GetRoute53Record
- SendALBARNs
- FindELBDifference
- SendELBDifferenceEmail
 
##### GetRoute53Record:
This lambda functions scans route 53 hosted zones and filter out the zone ID and search for records in that zone ID extract all A type records (elb dns only) and put them into a dynamodb table.
put picture of dynamodb data.

##### SendALBARNs:
This function scans for application load balancer having tags (enable=true, isPrimary=true and secondaryARN= "ARN-secondaryLoadbalancer") and creates batches and invoke FindELBDifference function for each batch.
##### FindELBDifference:
This functions finds difference in properties of primary and secondary load balanacers,
- Attributes differences
- Listeners differences
- Target groups differences
- Security group difference (ingress and egress)
- ALB Listener certificate
- Route 53 record name differences.

if this function finds any differences between 2 ELBs result is stored in form of json object into a dynamodb table.
##### SendELBDifferenceEmail:
This function is triggered after 15 minutes of SendALBARNs function, The results stored by FindELBDifference function is read by this function from dynamodb table and strcuture into an HTML format and sends an email of all the ELBs differences.
put picture here.

#### Resources:
- S3 Bucket configured to work as a static site containing report of differences.
- Dynamodb table to store Route53 DNS.
- Dynamodb table to store differences as a json

### Steps to Build and Deploy this app:
The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.
To build and deploy your application for the first time, run the following in your shell:
##### Step 1: Initialize sam project:
Run the command in you Linux terminal, 

```sam init```

choose custom Template Location and give path of you project zip file.
This command creates a directory with the name as the project name.

##### Step 2: Build your application:
First, change into the project directory, where the template.yaml file for the sample application is located. Then run this command:

```sam build```

or 

```sam build --use-container```

The SAM CLI installs dependencies defined in handlers/requirements.txt, creates a deployment package, and saves it in the .aws-sam/build folder.

##### Step 3: Deploy your application:
To deploy your application you can use following commands, use guided flag when you are deploying for the first time so it can setup all the configuratons in a guide way.

```sam deploy```

or 

``` sam deploy --guided```

