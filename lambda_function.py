import json
import boto3
import time
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
client = boto3.client('logs', region_name="us-east-1", aws_access_key_id=aws_config['aws_access_key_id'], aws_secret_access_key=aws_config['aws_secret_access_key'])
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('manager_mode')
image_store = dynamodb.Table('image_store')
logs = dynamodb.Table('logs')

def lambda_handler(event, context):
    response = table.get_item(Key={'app_name' : "manager_app"})
    message = ''
    
    if response.get('Item').get('automatic_mode'):
        # EC2 Train instance
        instance_ids = ['i-061843a216e13035b'] 
        
        response = ec2.describe_instances(InstanceIds=instance_ids)
        current_status = response['Reservations'][0]['Instances'][0]['State']['Name']
        message += "current_status of EC2 is: " + current_status
        if current_status == "stopped":
            response = image_store.scan()
            
            train_count = 0
            for item in response['Items']:
                if not item['label'] == None and item['trained'] == False:
                    train_count += 1
            message += '. Current train_count: ' + str(train_count)       
            if train_count >= 10:
                message += '[EC2 Starting]'
                
                try:
                    response = ec2.start_instances(InstanceIds=instance_ids)
                    message += str(response)
                except ClientError as e:
                    if 'DryRunOperation' not in str(e):
                        message += str(e)
    else:
        message += "EC2 instance not in stopped state" + str(response)
    create_log(message)
    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }
    
def create_log(message):
    sequence_token = None
    log_event = {
        'logGroupName': 'A3Logs',
        'logStreamName': 'ApplicationLogs',
        'logEvents': [
            {
                'timestamp': int(round(time.time() * 1000)),
                'message': str(message)
            },
        ],
    }

    log_stream_resp = client.describe_log_streams(logGroupName="A3Logs", logStreamNamePrefix="ApplicationLogs") 
    
    if 'uploadSequenceToken' in log_stream_resp['logStreams'][0]:
        # Get previous Sequence Token if it exists and add it to parameter
        sequence_token = log_stream_resp['logStreams'][0]['uploadSequenceToken']
        log_event['sequenceToken'] = sequence_token
        client.put_log_events(**log_event)

