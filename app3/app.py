from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

def save_pose_to_db(keypoints, angle, exercise, count, test_uuid, user_mrn):
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('INSERT INTO pose_estimations (keypoints, angle, exercise, count, test_uuid, user_mrn) VALUES (?, ?, ?, ?, ?, ?)', 
              (keypoints, angle, exercise, count, test_uuid, user_mrn))
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
