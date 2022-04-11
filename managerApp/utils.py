from access_key import aws_config
from botocore.exceptions import ClientError
import boto3, json, time
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
ec2 = boto3.client('ec2',config=my_config,aws_access_key_id= aws_config['aws_access_key_id'], aws_secret_access_key= aws_config['aws_secret_access_key'])

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

def update_dynamo(key, label):
    response = image_store.update_item(
        Key={
            'image_key': key,
        },
        UpdateExpression="set label=:l, trained=:t",
        ExpressionAttributeValues = {
            ':l': label,
            ':t': False
        },
        ReturnValues="UPDATED_NEW"
    )

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return "OK"
    return "FAILURE"

# update the manager mode
def update_dynamo_manager_mode(key, mode):
    
    value = False if mode == "Manual" else True
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
                            'predicted_label': item['predicted_label']
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


def read_all_keys():
    try:
        response = image_store.scan()
        list = []
        index = 1
        for item in response['Items']:
            list.append(
                {
                    'index': index,
                    'key': item['image_key'],
                    'label': item['label'],
                    'predicted_label': item['predicted_label']
                })
            index += 1
        return list
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


def startup(instance_id):
    print('Starting instance ' + instance_id)
    try:
        ec2.start_instances(InstanceIds=[instance_id], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            raise

    # Dry run succeeded, run start_instances without dryrun
    try:
        response = ec2.start_instances(InstanceIds=[instance_id], DryRun=False)
        print(response)
    except ClientError as e:
        print(e)

def read_model_metrics():
    data = s3.get_object(Bucket='ece1779model', Key='vgg_stats.json')["Body"].read().decode('utf-8')
    data = json.loads(data)
    return data

def check_training(instance_id):
    response = ec2.describe_instance_status(InstanceIds=[instance_id])
    if not len(response['InstanceStatuses']) == 0:
        if response['InstanceStatuses'][0]['InstanceState']['Name'] == 'running' or response['InstanceStatuses'][0]['InstanceState']['Name'] == 'pending':
            return True
    return False

def get_train_mode():
    response = manager_mode.get_item(Key={'app_name' : "manager_app"})
    
    return response.get('Item').get('automatic_mode')