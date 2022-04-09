import boto3
from botocore.config import Config
from tensorflow.python.keras.models import load_model
from access_key import aws_config
import json

S3_BUCKET = "image-bucket-a3"

my_config = Config(
    region_name = 'us-east-1',
    #signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

s3=boto3.client('s3', config=my_config, aws_access_key_id=aws_config['aws_access_key_id'], aws_secret_access_key=aws_config['aws_secret_access_key'])
dynamodb = boto3.resource('dynamodb', config=my_config, aws_access_key_id=aws_config['aws_access_key_id'], aws_secret_access_key= aws_config['aws_secret_access_key'])
image_store = dynamodb.Table('image_store')

def download_image(key):
    try:
        return s3.get_object(Bucket=S3_BUCKET, Key=key)["Body"].read()
    except:
        return None


def load_s3_model():
    s3.download_file('ece1779model', 'vgg_new.h5', 'vgg_new.h5')

    vgg_loaded = load_model('vgg_new.h5')
    return vgg_loaded

def save_s3_model(model, loss, accuracy):
    model.save('vgg_new.h5')  # creates a HDF5 file 'vgg_new.h5'
    s3.upload_file(Filename='vgg_new.h5',
                   Bucket='ece1779model',
                   Key='vgg_new.h5')
    
    
    json_data = {
        'loss': loss,
        'accuracy': accuracy
    }
    s3.put_object(Body=bytes(json.dumps(json_data).encode('UTF-8')),Key='vgg_stats.json',Bucket="ece1779model",ContentType='json')
    

def read_all():
    try:
        response = image_store.scan()
        key_list = []
        label_list = []
        
        for item in response['Items']:
            if item['trained'] == False and not item['label'] == None:
                key_list.append(item['image_key'])
                label_list.append(item['label'])
                    
        return key_list, label_list
    except:
        return None


def update_dynamo(key):
    response = image_store.update_item(
        Key={
            'image_key': key,
        },
        UpdateExpression="set trained=:t",
        ExpressionAttributeValues = {
            ':t': True
        },
        ReturnValues="UPDATED_NEW"
    )

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return "OK"
    return "FAILURE"

def load_s3_metrics():
    s3.download_file('ece1779model', 'vgg_stats.json', 'vgg_stats.json')
    with open('vgg_stats.json') as json_file:
        data = json.load(json_file)
    
    return data