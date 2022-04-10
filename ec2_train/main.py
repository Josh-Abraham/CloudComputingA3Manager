import tensorflow as tf
from aws_utils import load_s3_model, read_all, update_dynamo, read_metrics, write_same_metrics, shutdown
from model_utils import generate_image_tensor, retrain
from numpy import asarray
SELF_INSITANCE = 'i-061843a216e13035b' 

def retrain_call():
    print('RETRAIN')
    keys, labels = read_all()
    print(keys)
    if len(keys) > 0:
        model = load_s3_model()
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
    else:
        metrics = read_metrics()
        accuracy = metrics['accuracy']
        loss = metrics['loss']
        key = metrics['key'] + 1
        write_same_metrics(loss, accuracy, key)
        
retrain_call()
shutdown(SELF_INSITANCE)