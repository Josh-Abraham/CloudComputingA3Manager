from access_key import aws_config
import boto3
from botocore.config import Config

S3_BUCKET = "image-bucket-a3"
my_config = Config(
    region_name = 'us-east-1',
    #signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

s3=boto3.client('s3', config=my_config, aws_access_key_id= aws_config['aws_access_key_id'], aws_secret_access_key= aws_config['aws_secret_access_key'])
dynamodb = boto3.resource('dynamodb', config=my_config, aws_access_key_id= aws_config['aws_access_key_id'], aws_secret_access_key= aws_config['aws_secret_access_key'])
image_store = dynamodb.Table('image_store')

def download_image(key):
    try:
        return s3.get_object(Bucket=S3_BUCKET, Key=key)["Body"].read().decode('utf-8')
    except:
        return None

def read_dynamo(key):
    try:
        if not key == "":
            response = image_store.get_item(
            Key={
                    'image_key' : key,
                }
            )

            if 'Item' in response:
                return response['Item']
        return None
    except:
        return None

def update_dynamo(key, label, classification="None"):
    response = image_store.update_item(
        Key={
            'image_key': key,
        },
        UpdateExpression="set label=:l, predicted_label=:p, trained=:t",
        ExpressionAttributeValues = {
            ':l': label,
            ':p': classification,
            ':t': False
        },
        ReturnValues="UPDATED_NEW"
    )

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return "OK"
    return "FAILURE"

def scan_dynamo():
    metrics = {
        'untrained': 0,
        'labelled': 0,
        'trained': 0,
        'matching': 0
    }
    # full scan dynamo
    elems = []
    for image in elems:
        if image['trained'] == False:
            metrics['untrained'] += 1
            if not image['label'] == None:
                metrics['labelled'] += 1
            #unlabelled = untrained - labelled
        else:
            metrics['trained'] += 1
            if image['predicted_label'] == image['label']:
                metrics['matching'] += 1
            #not matching = trained - matching
    
    return metrics

def remove_metric(metrics, key, new_label):
    old_data = read_dynamo(key)
    if 'trained' in old_data:
        if old_data['trained']:
            metrics['untrained'] += 1
            metrics['trained'] -= 1

            if old_data['predicted_label'] == old_data['label'] and not old_data['label'] == new_label:
                metrics['matching'] -= 1
        
    if old_data['label'] == None:
        metrics['labelled'] += 1

def read_category(category, isPredicted):
    try:
        response = image_store.scan()
        images = [[]]
        i = 0
        j = 0
        for item in response['Items']:
            if isPredicted:
                if item['predicted_label'] == category:
                    images[i].append(
                        {
                            'image': download_image(item['image_key']),
                            'label': item['label'],
                            'label': item['label']
                        })
                    j += 1
                    if j % 3 == 0:
                        images.append([])
                        i += 1
                        j = 0
            else:
                if item['label'] == category:
                    images[i].append(
                        {
                            'image': download_image(item['image_key']),
                            'label': item['label'],
                            'predicted_label': item['predicted_label']
                        })
                    j += 1
                    if j % 3 == 0:
                        images.append([])
                        i += 1
                        j = 0
        return images
    except:
        return None