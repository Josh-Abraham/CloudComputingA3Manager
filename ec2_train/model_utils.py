import tensorflow as tf
import tensorflow_datasets as tfds
from PIL import Image
from numpy import asarray
from aws_utils import download_image, save_s3_model, load_s3_metrics
import base64

split = ['train[:97%]', 'train[97%:]']
trainDataset, testDataset = tfds.load(name='cats_vs_dogs', split=split, as_supervised=True)
HEIGHT = 200
WIDTH = 200

def generate_image_tensor(key):
    global HEIGHT, WIDTH

    base64_image = download_image(key)
    with open("image.png", "wb") as fh:
        fh.write(base64.decodebytes(base64_image))
    image = Image.open('image.png')
    image.load() # required for png.split()

    # For RGBA
    if len(image.split()) == 4:
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3]) # 3 is the alpha channel
        image = background

    image_array = tf.keras.preprocessing.image.img_to_array(image)
    image_tf = tf.image.resize_with_pad(image_array, HEIGHT, WIDTH) / 255
    
    image_tf = tf.reshape(image_tf, [1, HEIGHT, WIDTH, 3])

    return image_tf

def preprocess(img, label):
    return tf.image.resize(img, [HEIGHT, WIDTH]) / 255, label
trainDataset = trainDataset.map(preprocess).batch(32)
testDataset = testDataset.map(preprocess).batch(32)


def compute_loss(model,images, labels):
  """Compute loss for given images
     and labels.

  Args:
    images: Tensor representing a batch of images.
    labels: Tensor representing a batch of labels.

  Returns:
    Scalar loss Tensor.
  """
  output = model(images, training=True)
  # Compute cross-entropy loss for subclasses.

  # your code start from here for step 3
  
  loss = tf.keras.losses.CategoricalCrossentropy(axis=-1,name='categorical_crossentropy')
  cross_entropy_loss_value = loss(labels,output)


  return cross_entropy_loss_value


def retrain(model, images, labels):
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)

    for epoch in range(1, 3 + 1):
        # Run training.
        print('Epoch {}: '.format(epoch), end='')
        with tf.GradientTape() as tape:
            for i in range(len(images)):
                loss_value = compute_loss(model,images[i],labels[i])

        grads = tape.gradient(loss_value, model.trainable_variables)
        optimizer.apply_gradients(zip(grads, model.trainable_variables))

    # Run evaluation.
    (loss, accuracy) = model.evaluate(testDataset)
    accuracy_old = load_s3_metrics()['accuracy']
    if accuracy >= accuracy_old:
        save_s3_model(model, loss, accuracy)
        return "OK"
    return "Not Updated"