from flask import Blueprint, render_template, request, redirect
from utils import *

manager_routes = Blueprint("manager_routes", __name__)
MODEL_METRICS = scan_dynamo()
IMAGE = None
PREDICTION = None
LABEL = None

@manager_routes.route('/label_image', methods = ['GET','POST'])
def label_image():
    """Label an image
    Given a search exists give classification option
    Write to dynamo, include new 'trained' tag
    """
    global IMAGE, PREDICTION, MODEL_METRICS, LABEL
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
            remove_metric(MODEL_METRICS, key, category)
            resp = update_dynamo(key, category)
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
    if request.method == 'POST':
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
    return render_template("settings.html")

@manager_routes.route('/clear_data', methods = ['GET', 'POST'])
def clear_data():
    # clear dynamo
    # clear S3
    return redirect('/settings')

@manager_routes.route('/clear_labels', methods = ['GET', 'POST'])
def clear_labels():
    # set dynamo labels to "None"
    return redirect('/settings')