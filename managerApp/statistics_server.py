import requests
import boto3, time, datetime, json
from access_key import aws_config
client = boto3.client('logs', region_name="us-east-1", aws_access_key_id=aws_config['aws_access_key_id'], aws_secret_access_key=aws_config['aws_secret_access_key'])

def create_log(message):
    sequence_token = None
    log_event = {
        'logGroupName': 'A3Logs',
        'logStreamName': 'ApplicationLogs',
        'logEvents': [
            {
                'timestamp': int(round(time.time() * 1000)),
                'message': message
            },
        ],
    }

    log_stream_resp = client.describe_log_streams(logGroupName="A3Logs", logStreamNamePrefix="ApplicationLogs") 
    
    if 'uploadSequenceToken' in log_stream_resp['logStreams'][0]:
        # Get previous Sequence Token if it exists and add it to parameter
        sequence_token = log_stream_resp['logStreams'][0]['uploadSequenceToken']
        log_event['sequenceToken'] = sequence_token

    try:
        client.put_log_events(**log_event)
    except Exception as e:
        sequence_token = e.response['expectedSequenceToken']
        log_event['sequenceToken'] = sequence_token
        client.put_log_events(**log_event)
