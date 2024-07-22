from flask import Flask, request, jsonify, render_template, Response
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

@app.route('/upload_video', methods=['POST'])
def upload_video():
    video = request.files['video']
    test_uuid = request.form['test_uuid']
    user_mrn = request.form['user_mrn']
    output_type = request.form['output_type']
    
    video_blob = video.read()

    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('INSERT INTO videos (test_uuid, user_mrn, video, output_type) VALUES (?, ?, ?, ?)', 
              (test_uuid, user_mrn, video_blob, output_type))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/videos', methods=['GET'])
def get_videos():
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('SELECT id, test_uuid, output_type FROM videos')
    data = c.fetchall()
    conn.close()
    return jsonify([{'id': row[0], 'name': f"{row[1]}_{row[2]}"} for row in data])

@app.route('/video/<int:video_id>', methods=['GET'])
def get_video(video_id):
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('SELECT video FROM videos WHERE id = ?', (video_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return Response(row[0], mimetype='video/mp4')
    return 'Video not found', 404

@app.route('/video_metadata/<int:video_id>', methods=['GET'])
def get_video_metadata(video_id):
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()

    try:
        # Get video metadata
        c.execute('SELECT video, test_uuid, user_mrn FROM videos WHERE id = ?', (video_id,))
        video_row = c.fetchone()

        if not video_row:
            return jsonify({'error': 'Video not found'}), 404

        video_blob, test_uuid, user_mrn = video_row

        # Get session details
        c.execute('SELECT angle, count, exercise FROM pose_estimations WHERE test_uuid = ?', (test_uuid,))
        pose_rows = c.fetchall()

        # Get the maximum count
        max_count = (max([row[1] for row in pose_rows])) + 1 if pose_rows else 0

        # Fetch user details
        c.execute('SELECT first_name, last_name FROM users WHERE mrn = ?', (user_mrn,))
        user_row = c.fetchone()

        user_name = f"{user_row[0]} {user_row[1]}" if user_row else "Unknown User"

        metadata = {
            'test_uuid': test_uuid,
            'user_name': user_name,
            'exercise': pose_rows[0][2] if pose_rows else 'N/A',
            'movement_count': max_count,
            'pose_data': pose_rows
        }

        return jsonify(metadata)
    finally:
        conn.close()


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
