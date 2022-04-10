from cmath import exp
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
manager_mode = dynamodb.Table('manager_mode')

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

def read_dynamo_manager_mode(key):
    try:
        if not key == "":
            response = manager_mode.get_item(Key={'app_name' : "manager_app"})
            print("response in read is: ", response)
            if 'Item' in response:
                return response['Item']['automatic_mode']
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

# update the manager mode
def update_dynamo_manager_mode(key, mode):
    value = False if mode == "manual" else True
    response = manager_mode.update_item(Key={'app_name': key},
        UpdateExpression="set automatic_mode=:m",ExpressionAttributeValues = {':m': value},
            ReturnValues="UPDATED_NEW")
    print("response is : ", response)
    print("current value at dynamo_db is: ", read_dynamo_manager_mode('manager_app'))
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return "OK"
    return "FAILURE"


def get_metrics():
    metrics = {
        'untrained': 0,
        'labelled': 0,
        'trained': 0,
        'matching': 0
    }
    # full scan dynamo
    response = image_store.scan()
    elems = response['Items']
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

def read_all():
    try:
        response = image_store.scan()
        images = [[]]
        i = 0
        j = 0
        for item in response['Items']:
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
        return images
    except:
        return None

def purge_images():
    s3_del = boto3.resource('s3',config=my_config,aws_access_key_id= aws_config['aws_access_key_id'], aws_secret_access_key= aws_config['aws_secret_access_key'])
    bucket = s3_del.Bucket(S3_BUCKET)
    bucket.objects.all().delete()
    return True
    
def clear_table():
    global image_store
    response = image_store.scan()
    elems = response['Items']
    for elem in elems:
        key = elem['image_key']
        response = image_store.delete_item(
                Key={
                    'image_key': key
                }
            )
    return {
        'untrained': 0,
        'labelled': 0,
        'trained': 0,
        'matching': 0
    }


