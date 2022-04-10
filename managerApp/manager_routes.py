from flask import Blueprint, render_template, request
from utils import *

manager_routes = Blueprint("manager_routes", __name__)
DATA_METRICS = get_metrics()

MODEL_TRAINING = False
IMAGE = None
PREDICTION = None
LABEL = None
TRAIN_INSTANCE = 'i-061843a216e13035b'

@manager_routes.route('/label_image', methods = ['GET','POST'])
def label_image():
    """Label an image
    Given a search exists give classification option
    Write to dynamo, include new 'trained' tag
    """
    global IMAGE, PREDICTION, DATA_METRICS, LABEL
    if request.method == 'POST':
        category = request.form.get("submit")
        if category == None:
            key = request.form.get('key')
            resp = read_dynamo(key)
            if not resp == None:
                IMAGE = download_image(key)
                if not IMAGE == None:
                    PREDICTION = resp['predicted_label']
                    LABEL = resp['label']
                    return render_template("label_image.html", image=IMAGE, prediction=PREDICTION, label=LABEL, key=key)
            # No Key -> Returns Not Found 
            return render_template("label_image.html", status="No Image With Provided Key", key=key)
        else:
            # On dropdown click
            key = request.form.get('key')
            resp = update_dynamo(key, category)
            DATA_METRICS = get_metrics()
            if resp == "OK":
                LABEL=category
                return render_template("label_image.html", image=IMAGE, prediction=PREDICTION, label=LABEL, key=key)
            return render_template("label_image.html", status="Error writing new label", key=key)


    return render_template("label_image.html")

@manager_routes.route('/show_category', methods = ['GET', 'POST'])
def show_category():
    """Show all images
    GET: Simply render the show_image page
    POST: Search for a given key
    """
    if request.method == 'GET':
        images = read_all()
        if (not images == None) and len(images[0]) == 0:
                return render_template("show_category.html", status=405)
        return render_template("show_category.html", images=images, showAll=True)
    elif request.method == 'POST':
        predict_category = request.form.get("submit-predict")
        label_category = request.form.get("submit-label")
        if not predict_category == None:
            images = read_category(predict_category, True)
            if (not images == None) and len(images[0]) == 0:
                return render_template("show_category.html", status=404)
            return render_template("show_category.html", images=images)
        elif not label_category == None:
            images = read_category(label_category, False)
            if (not images == None) and len(images[0]) == 0:
                return render_template("show_category.html", status=404)
            return render_template("show_category.html", images=images)
        
    return render_template("show_category.html")

@manager_routes.route('/settings', methods = ['GET', 'POST'])
def settings():
    global TRAIN_INSTANCE, MODEL_TRAINING
    model_metrics = read_model_metrics()
    accuracy = model_metrics['accuracy']
    loss = model_metrics['loss']
    MODEL_TRAINING = check_training(TRAIN_INSTANCE)

    if request.method == 'GET':
        train_metrics, label_metrics = configure_metrics()
        return render_template("settings.html", train_metrics=train_metrics, label_metrics=label_metrics, accuracy=accuracy, loss=loss, isTraining=MODEL_TRAINING)
    
    is_clear = request.form.get("clear_data")
    if not is_clear == None:
        clear_table()
        purge_images()
        train_metrics, label_metrics = configure_metrics()
        return render_template("settings.html", train_metrics=train_metrics, label_metrics=label_metrics, accuracy=accuracy, loss=loss, isTraining=MODEL_TRAINING)
    
    print('train_model')
    MODEL_TRAINING = True
    startup(TRAIN_INSTANCE)
    
    train_metrics, label_metrics = configure_metrics()
    return render_template("settings.html", train_metrics=train_metrics, label_metrics=label_metrics, accuracy=accuracy, loss=loss, isTraining=MODEL_TRAINING)


@manager_routes.route('/list_images')
def list_images():
    """ Get list of all keys currently in the database
    """
    image_list = read_all_keys()
    total=len(image_list)

    if not image_list == None:
        return render_template('list_images.html', image_list=image_list, total=total)
    else:
        return render_template('list_images.html')

### Helper Functions

def configure_metrics():
    global DATA_METRICS
    DATA_METRICS = get_metrics()
    train_metrics = [
        {'name': 'Untrained', 'value': DATA_METRICS['untrained']},
        {'name': 'Trained', 'value': DATA_METRICS['trained']}
    ]
    label_metrics = [
        {'name': 'Labelled', 'value': DATA_METRICS['labelled']},
        {'name': 'Unlabelled', 'value': DATA_METRICS['untrained'] - DATA_METRICS['labelled']},
        {'name': 'Matching', 'value': DATA_METRICS['matching']},
        {'name': 'Not Matching', 'value': DATA_METRICS['trained'] - DATA_METRICS['matching']},
    ]
    return train_metrics, label_metrics