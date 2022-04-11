import json
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

my_config = Config(
    region_name = 'us-east-1',
    #signature_version = 'v4',
    retries = {'max_attempts': 10,'mode': 'standard'
    })
aws_config = {
    'aws_access_key_id': 'AKIA3U4U6D42PLQZVFOX',
    'aws_secret_access_key': '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'
    
}
ec2 = boto3.client('ec2', config=my_config,aws_access_key_id= aws_config['aws_access_key_id'], aws_secret_access_key= aws_config['aws_secret_access_key'])
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('manager_mode')

def lambda_handler(event, context):
    response = table.get_item(Key={'app_name' : "manager_app"})
    message = ''
    
    if response.get('Item').get('automatic_mode'):
        # EC2 Train instance
        instance_ids = ['i-061843a216e13035b'] 
        response = ec2.describe_instances(InstanceIds=instance_ids)
        current_status = response['Reservations'][0]['Instances'][0]['State']['Name']
  
        if current_status == "stopped":
            message += '[EC2 Starting]'
            try:
                response = ec2.start_instances(InstanceIds=instance_ids, DryRun=True)
                message += response
            except ClientError as e:
                if 'DryRunOperation' not in str(e):
                    message += str(e)
                    raise
        
            # Dry run succeeded, run start_instances without dryrun
            try:
                response = ec2.start_instances(InstanceIds=instance_ids, DryRun=False)
                message += str(response)
            except ClientError as e:
                message += str(e)
    else:
        message += str(response)
    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }