from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

def save_pose_to_db(keypoints, angle, exercise, count):
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('INSERT INTO pose_estimations (keypoints, angle, exercise, count) VALUES (?, ?, ?, ?)', (keypoints, angle, exercise, count))
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
    if keypoints and angle is not None and exercise and count is not None:
        save_pose_to_db(keypoints, angle, exercise, count)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'failure'}), 400

@app.route('/get_poses', methods=['GET'])
def get_poses():
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('SELECT * FROM pose_estimations')
    poses = c.fetchall()
    conn.close()
    return jsonify({'poses': poses})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5007)
