import requests
import boto3, time, datetime, json
from access_key import aws_config
client = boto3.client('logs', region_name="us-east-1", aws_access_key_id=aws_config['aws_access_key_id'], aws_secret_access_key=aws_config['aws_secret_access_key'])

def create_log(message):
    sequence_token = None
    log_stream_resp = client.describe_log_streams(logGroupName="MetricLogsA3", logStreamNamePrefix="ApplicationLogs")
    if 'uploadSequenceToken' in log_stream_resp['logStreams'][0]:
        # Get previous Sequence Token if it exists
        sequence_token = log_stream_resp['logStreams'][0]['uploadSequenceToken']

    log_event = {
            'logGroupName': 'MetricLogs',
            'logStreamName': 'ApplicationLogs',
            'logEvents': [
                {
                    'timestamp': int(round(time.time() * 1000)),
                    'message': message
                },
            ],
        }
    if sequence_token:
        log_event['sequenceToken'] = sequence_token

    try:
        client.put_log_events(**log_event)
    except:
        print("")
