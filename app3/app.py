from flask import Flask, request, jsonify, render_template, Response, send_from_directory
import sqlite3
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_pose_to_db(keypoints, angle, exercise, count, test_uuid, user_mrn):
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('INSERT INTO pose_estimations (keypoints, angle, exercise, count, test_uuid, user_mrn) VALUES (?, ?, ?, ?, ?, ?)', 
              (keypoints, angle, exercise, count, test_uuid, user_mrn))
    conn.commit()
    conn.close()

def save_video_to_db(test_uuid, user_mrn, video_path):
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    with open(video_path, 'rb') as file:
        video = file.read()
    c.execute('INSERT INTO video_sessions (test_uuid, user_mrn, video) VALUES (?, ?, ?)', 
              (test_uuid, user_mrn, video))
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/capture', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/save_pose', methods=['POST'])
def save_pose():
    data = request.json
    keypoints = data.get('keypoints', None)
    angle = data.get('angle', None)
    exercise = data.get('exercise', None)
    count = data.get('count', None)
    test_uuid = data.get('test_uuid', None)
    user_mrn = data.get('user_mrn', None)
    if keypoints and angle is not None and exercise and count is not None and test_uuid and user_mrn:
        save_pose_to_db(keypoints, angle, exercise, count, test_uuid, user_mrn)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'failure'}), 400

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'status': 'failure', 'message': 'No video file provided'}), 400

    video = request.files['video']
    test_uuid = request.form.get('test_uuid')
    user_mrn = request.form.get('user_mrn')

    if video and test_uuid and user_mrn:
        filename = secure_filename(video.filename)
        video_path = os.path.join('uploads', filename)
        video.save(video_path)
        save_video_to_db(test_uuid, user_mrn, video_path)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'failure'}), 400

@app.route('/videos', methods=['GET'])
def list_videos():
    videos = os.listdir(app.config['UPLOAD_FOLDER'])
    videos_info = [{'name': video, 'path': f'/uploads/{video}'} for video in videos]
    return jsonify(videos_info)

@app.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/watch', methods=['GET'])
def watch():
    return render_template('watch.html')


@app.route('/get_poses', methods=['GET'])
def get_poses():
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('SELECT * FROM pose_estimations')
    poses = c.fetchall()
    conn.close()
    return jsonify({'poses': poses})

@app.route('/visualize', methods=['GET'])
def visualize():
    return render_template('visualize.html')

@app.route('/get_pose_data', methods=['GET'])
def get_pose_data():
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('SELECT timestamp, angle, exercise, count, test_uuid, user_mrn FROM pose_estimations ORDER BY timestamp')
    data = c.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/get_users', methods=['GET'])
def get_users():
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('SELECT mrn, first_name, last_name FROM users')
    data = c.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/table', methods=['GET'])
def table():
    return render_template('table.html')

@app.route('/table_non_pivot', methods=['GET'])
def table_non_pivot():
    return render_template('table_non_pivot.html')

@app.route('/get_non_pivot_data', methods=['GET'])
def get_non_pivot_data():
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('SELECT timestamp, angle, exercise, count, test_uuid, user_mrn FROM pose_estimations ORDER BY timestamp')
    data = c.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/get_pivot_data', methods=['GET'])
def get_pivot_data():
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('SELECT test_uuid, count, exercise, user_mrn, GROUP_CONCAT(angle) as angles FROM pose_estimations GROUP BY test_uuid, count, exercise, user_mrn ORDER BY timestamp')
    data = c.fetchall()
    conn.close()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5007)
