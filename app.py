import os
from flask import Flask, render_template, request, redirect, send_from_directory,session
from werkzeug.utils import secure_filename
import torch
import cv2
from PIL import Image
from torchvision.transforms import functional as F
from pymongo import MongoClient
from bson.objectid import ObjectId
from twilio.rest import Client
import random
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('KEY')  # Replace with your own secret key

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STATIC_FOLDER'] = 'static'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

model = torch.hub.load('ultralytics/yolov5', 'custom', path='bestendo.pt')
modelmic = torch.hub.load('ultralytics/yolov5', 'custom', path='./best (1).pt')
client = MongoClient(os.getenv('DATABASE'))
db = client['database']
users_collection = db['users']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def predict(image_path):
    img = Image.open(image_path)
    img = img.convert('RGB')
    img = F.resize(img, (200, 200))
    img.save('uploads/temp.png')
    img.save('static/temp.png')

    results = model([img])
    predictions = results.pred[0]
    mask = predictions[:, 4] > 0.1
    predictions = predictions[mask]
    class_counts = {
        'class0': 0,
        'class1': 0,
        'class2': 0,
        'class3': 0
    }
    for pred in predictions:
        class_id = int(pred[5])
        if class_id >= 0 and class_id < 4:
            class_counts[f'class{class_id}'] += 1
     
    predicted_img = results.render(labels=False)[0]
    cv2.imwrite('uploads/predicted.png', predicted_img[:, :, ::-1])
    cv2.imwrite('static/predicted.png', predicted_img[:, :, ::-1])
    filename = os.path.basename(image_path)
    return 'predicted.png', filename, class_counts


def predictendo(image_path):
    img = Image.open(image_path)
    img = img.convert('RGB')
    img = F.resize(img, (200, 200))
    img.save('uploads/temp.png')
    img.save('static/temp.png')

    results = model([img])
    predictions = results.pred[0]
    mask = predictions[:, 4] > 0.1
    predictions = predictions[mask]
    predicted_img = results.render(labels=False)[0]
    cv2.imwrite('uploads/predicted.png', predicted_img[:, :, ::-1])
    cv2.imwrite('static/predicted.png', predicted_img[:, :, ::-1])
    filename = os.path.basename(image_path)
    return 'predicted.png', filename


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = users_collection.find_one({'email': email}) # Authentication
        if user and user['password'] == password:
            return redirect('/index')
        else:
            error = 'Invalid login credentials'
            return render_template('login.html', error=error)

    return render_template('login.html')

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
clients = Client(account_sid, auth_token)
otp_data = {}

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        session['email'] = email  
        password = request.form.get('password')
        re_password = request.form.get('re_password')
        phone = request.form.get('phone')
        if password != re_password:
            error = 'Passwords do not match'
            return render_template('signup.html', error=error)
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            error = 'User already exists'
            return render_template('signup.html', error=error)
        otp = str(random.randint(1000, 9999))
        print("Generated OTP:", otp)
        print("Phone number:", phone)
        otp_data['+91'+phone] = otp
        users_collection.insert_one({'email': email, 'password': password, 'phone': '+91'+phone, 'otp': otp})
        message = clients.messages.create(
            body=f'Your OTP: {otp}',
            from_=twilio_phone_number,
            to='+91'+phone
        )
        return redirect('/otp')
    return render_template('signup.html')

@app.route('/otp', methods=['GET', 'POST'])
def otp():
    if request.method == 'POST':
        otp = request.form.get('otp')
        email = session.get('email')
        user = users_collection.find_one({'email': email})
        stored_otp = user.get('otp') if user else None
        if otp == stored_otp:
            return redirect('/')
        else:
            error = 'Invalid OTP. Please try again.'
            return render_template('otp.html', error=error)
    return render_template('otp.html')


@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/result/<filename>')
def result(filename):
    return render_template('result.html', uploaded_filename=filename)

@app.route('/predicted/<filename>')
def predicted(filename):
    return send_from_directory('predicted', filename)

@app.route('/static/<filename>')
def ground_truth(filename):
    return send_from_directory('static', filename)

@app.route('/breast', methods=['GET', 'POST'])
def breast():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            predicted_image, uploaded_filename,class_counts= predict(file_path)
            return render_template('resbr.html', uploaded_filename=uploaded_filename, predicted_image=predicted_image,class_counts=class_counts)
    return render_template('br.html')

@app.route('/endonuke', methods=['GET', 'POST'])
def endonuke():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            predicted_image, uploaded_filename= predictendo(file_path)
            return render_template('result.html', uploaded_filename=uploaded_filename, predicted_image=predicted_image)
    return render_template('endo.html')
def predictmic(image_path):
    # Preprocess the image
    img = Image.open(image_path)
    img = img.convert('RGB')
    img.save('uploads/temp.jpg')
    img.save('static/temp.jpg')
    results = modelmic('uploads/temp.jpg')
    preds = results.xyxy[0].numpy()
    # Draw bounding boxes
    img = cv2.imread('uploads/temp.jpg')
    for pred in preds:
        x_min, y_min, x_max, y_max = pred[:4]
        cv2.rectangle(img, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 0, 255), 2)
    cv2.imwrite('uploads/predicted.jpg', img)
    cv2.imwrite('static/predicted.jpg', img)
    filename = os.path.basename(image_path)
    
    return 'predicted.jpg', filename

@app.route('/miccai', methods=['GET', 'POST'])
def miccai():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            predicted_image, uploaded_filename = predictmic(file_path)
            return render_template('resultmic.html', predicted_image_path=predicted_image, uploaded_filename=uploaded_filename)
    return render_template('mic.html')


if __name__ == '__main__':
    app.run(debug=True)
