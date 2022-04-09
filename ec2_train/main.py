import tensorflow as tf
from aws_utils import load_s3_model, read_all, update_dynamo
from model_utils import generate_image_tensor, retrain
from numpy import asarray


def retrain_call():
    print('RETRAIN')
    model = load_s3_model()
    keys, labels = read_all()
    if len(keys) > 0:
        image_tensors, label_tensors = [], []
        for key in keys:
            image_tf = generate_image_tensor(key)
            image_tensors.append(image_tf)
        
        for label in labels:
            if label == 'Cat':
                label_tf = tf.constant([[0.]])
            else:
                label_tf =  tf.constant([[1.]])
            
            label_tensors.append(label_tf)
        
        result = retrain(model, image_tensors, label_tensors)
        if result == "OK":
            for key in keys:
                update_dynamo(key)

        
retrain_call()
# Call lambda endpoint
# Call ec2 shutdown