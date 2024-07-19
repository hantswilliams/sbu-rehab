from flask import Flask, render_template, Response, request, redirect, jsonify, session, url_for
from flask_sqlalchemy import SQLAlchemy

from movements.pose_left import left_curl
from movements.pose_right import right_curl
from movements.pose_pushup import pushup
from movements.pose_squat import squat

from exercises.utils import process_exercise_frame
from PoseModule import poseDetector
import base64
from PIL import Image
from io import BytesIO

import cv2
import mediapipe as mp
import numpy as np
import os

exercise_completed = False  # Global variable to track exercise completion

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_mrn = db.Column(db.String(100), unique=True, nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)

# Create the database and add some initial data
with app.app_context():
    db.create_all()
    if User.query.count() == 0:
        users = [
            User(patient_mrn='MRN3bAA434', patient_name='Alex Smith'),
            User(patient_mrn='MRN3bAA435', patient_name='John Doe'),
            User(patient_mrn='MRN3bAA436', patient_name='Fred Johnson'),
            User(patient_mrn='MRN3bAA437', patient_name='Peter Parker'),
            User(patient_mrn='MRN3bAA438', patient_name='Clark Kent'),
            User(patient_mrn='MRN3bAA439', patient_name='Bruce Wayne'),
            User(patient_mrn='MRN3bAA440', patient_name='Tony Stark'),
        ]
        db.session.add_all(users)
        db.session.commit()

@app.route('/', methods=['GET'])
def index():
    users = User.query.all()
    return render_template('exercises.html', users=users)

@app.route('/check_completion')
def check_completion():
    global exercise_completed
    print('Global Status: ', exercise_completed)
    return jsonify({'exercise_completed': 'success' if exercise_completed else 'failure'}) 

@app.route('/set_completion', methods=['POST'])
def set_completion():
    global exercise_completed
    exercise_completed = True
    print('Set Global Status TO TRUE!')
    return jsonify({'exercise_completed': 'success'})

@app.route('/reset_completion', methods=['GET'])
def reset_completion():
    global exercise_completed
    exercise_completed = False
    print('Set Global Status TO FALSE!')
    return jsonify({'exercise_completed': 'failure'})

@app.route('/video/<subject>/<patient_name>/<patient_mrn>/<max_range_of_motion>/<expected_count>')
def video(subject, patient_name, patient_mrn, max_range_of_motion, expected_count):
    return render_template(
        'video2.html', 
        subject=subject,
        patient_name=patient_name,
        patient_mrn=patient_mrn,
        max_range_of_motion=max_range_of_motion,
        expected_count=expected_count    
    )

@app.route('/process_frame', methods=['POST'])
def process_frame():
    global exercise_completed
    data = request.json
    image_data = data.get('image')
    exercise_type = data.get('exercise_type')
    patient_mrn = data.get('patient_mrn')
    patient_name = data.get('patient_name')
    max_range_of_motion = float(data.get('max_range_of_motion', 0.0))
    expected_count = int(data.get('expected_count', 0))
    count = int(data.get('count', 0))
    direction = int(data.get('direction', 0))
    max_per = float(data.get('max_per', 0.0))
    movement_start_time = float(data.get('movement_start_time', 0.0))
    angle_change_count = int(data.get('angle_change_count', 0))
    previous_angle = float(data.get('previous_angle', 0.0)) if data.get('previous_angle') else None
    movements = data.get('movements', [])
    frames_for_gif = data.get('frames_for_gif', [])
    meta_session_id = data.get('meta_session_id')

    # Debugging logs
    if not image_data:
        print("No image data received.")
        return jsonify({"error": "No image data received"}), 400

    print("Received Base64 Data: ", image_data[:100])  # Log the first 100 characters of the base64 string

    try:
        image = np.array(Image.open(BytesIO(base64.b64decode(image_data))))
    except Exception as e:
        print(f"Error decoding image: {e}")
        return jsonify({"error": f"Failed to decode image data: {e}"}), 400

    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    detector = poseDetector()
    result = process_exercise_frame(
        exercise_type, image, detector, patient_mrn, patient_name, meta_session_id, max_range_of_motion, expected_count, count, direction, max_per, movement_start_time, movements, angle_change_count, previous_angle, frames_for_gif)

    if result is None:
        return jsonify({"error": "Failed to process frame"}), 500

    jpeg, count, direction, max_per, movement_start_time, movements, angle_change_count, previous_angle, frames_for_gif = result

    _, jpeg_encoded = cv2.imencode('.jpg', jpeg)  # Ensure the image is encoded correctly

    if count >= expected_count:
        exercise_completed = True

    return jsonify({
        'image': base64.b64encode(jpeg_encoded).decode('utf-8'),  # Encode the image back to base64
        'count': count,
        'direction': direction,
        'max_per': max_per,
        'movement_start_time': movement_start_time,
        'angle_change_count': angle_change_count,
        'previous_angle': previous_angle,
        'movements': movements,
        'frames_for_gif': frames_for_gif,
        'exercise_completed': exercise_completed
    })


@app.route('/show')
def show():
    subject = request.args.get('sub')
    patient_mrn = request.args.get('username')
    max_range_of_motion = request.args.get('max_range_of_motion')
    expected_count = request.args.get('expected_count')

    ## find matching user.patient_mrn for the given username
    user = User.query.filter_by(patient_mrn=patient_mrn).first()
    if user:
        patient_name = user.patient_name
    else:
        patient_name = 'Unknown Patient Name'

    return redirect(url_for(
        'video', subject=subject, patient_name=patient_name, patient_mrn=patient_mrn, max_range_of_motion=max_range_of_motion, expected_count=expected_count
        ))




@app.route('/video_feed_left')
def video_feed_left():

    patient_name = request.args.get('patient_name')
    patient_mrn = request.args.get('patient_mrn')
    max_range_of_motion = request.args.get('max_range_of_motion')
    expected_count = request.args.get('expected_count')

    return Response(left_curl(patient_mrn, patient_name, "left_curl", float(max_range_of_motion), int(expected_count)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_right')
def video_feed_right():

    patient_name = request.args.get('patient_name')
    patient_mrn = request.args.get('patient_mrn')
    max_range_of_motion = request.args.get('max_range_of_motion')
    expected_count = request.args.get('expected_count')

    return Response(right_curl(patient_mrn, patient_name, "right_curl", float(max_range_of_motion), int(expected_count)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_pushup')
def video_feed_pushup():

    patient_name = request.args.get('patient_name')
    patient_mrn = request.args.get('patient_mrn')
    max_range_of_motion = request.args.get('max_range_of_motion')
    expected_count = request.args.get('expected_count')

    return Response(pushup(patient_mrn, patient_name, "pushup", float(max_range_of_motion), int(expected_count)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_squat')
def video_feed_squat():

    patient_name = request.args.get('patient_name')
    patient_mrn = request.args.get('patient_mrn')
    max_range_of_motion = request.args.get('max_range_of_motion')
    expected_count = request.args.get('expected_count')

    return Response(squat(patient_mrn, patient_name, "squat", float(max_range_of_motion), int(expected_count)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')






@app.route('/metrics', methods=['GET'])
def metrics():
    return render_template('metrics.html')

@app.route('/metrics/raw', methods=['GET'])
def metrics_page():
    return render_template('metrics_raw.html')

@app.route('/metrics/visualization', methods=['GET'])
def visualization():
    users = User.query.all()
    return render_template('metrics_visual.html', users=users)

@app.route('/metrics/data', methods=['GET'])
def metrics_data():
    try:
        movements = []
        for file in os.listdir('./data'):
            if file.endswith(".npy"):
                data = np.load(f'./data/{file}', allow_pickle=True).item()
                movements.append(data)
        return jsonify(movements)
    except FileNotFoundError:
        return jsonify({"error": "No data available"}), 404
    
@app.route('/get_metrics/<patient_mrn>', methods=['GET'])
def get_metrics(patient_mrn):
    try:
        movements = []
        for file in os.listdir('./data'):
            if file.endswith(".npy"):
                data = np.load(f'./data/{file}', allow_pickle=True).item()
                if data['meta_patient_mrn'] == patient_mrn:
                    movements.append(data)
        return jsonify(movements)
    except FileNotFoundError:
        return jsonify({"error": "No data available"}), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", 
            port=5007,
            debug=True)
