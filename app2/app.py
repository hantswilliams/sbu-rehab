# from flask import Flask, render_template, Response, request
# import cv2
# import numpy as np
# from posemodule import poseDetector

# app = Flask(__name__)
# detector = poseDetector()

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/video_feed', methods=['POST'])
# def video_feed():
#     file = request.files.get('video')
#     if file:
#         data = file.read()
#         np_arr = np.frombuffer(data, np.uint8)
#         img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

#         if img is not None:
#             img = detector.findPose(img)
#             ret, jpeg = cv2.imencode('.jpg', img)
#             frame = jpeg.tobytes()
#             return Response(frame, mimetype='image/jpeg')
#         else:
#             print("Failed to decode image.")
#             return '', 204
#     else:
#         print("No video file received.")
#         return 'No video file received', 400

# if __name__ == "__main__":
#     app.run(
#         debug=True,
#         host='0.0.0.0',
#         port=5007
#     )


from flask import Flask, render_template, request, Response, redirect, url_for
import cv2
import numpy as np
import time
import uuid
import os
from posemodule import poseDetector

app = Flask(__name__)
app.secret_key = 'supersecretkey'
detector = poseDetector()

# Store session state
session_state = {
    'start_time': time.time(),
    'countdown': 3,
    'count': 0,
    'direction': 0,
    'form': 0,
    'feedback': "",
    'feedback_color': (0, 0, 0),
    'max_per': 0,
    'movements': [],
    'angle_change_count': 0,
    'previous_angle': None,
    'movement_start_time': time.time(),
    'frames_for_gif': [],
    'patient_mrn': '1234',
    'patient_name': 'john-doe',
    'exercise_type': 'left curl',
    'max_range_of_motion': 0.50,
    'expected_count': 5,
    'meta_session_id': "POSELEFT-" + str(uuid.uuid4())[:4] + "-" + str(uuid.uuid4())[:4],
    'exercise_date': time.strftime("%Y-%m-%d %H:%M:%S")
}

def reset_session_state():
    global session_state
    session_state.update({
        'start_time': time.time(),
        'countdown': 3,
        'count': 0,
        'direction': 0,
        'form': 0,
        'feedback': "",
        'feedback_color': (0, 0, 0),
        'max_per': 0,
        'movements': [],
        'angle_change_count': 0,
        'previous_angle': None,
        'movement_start_time': time.time(),
        'frames_for_gif': [],
        'meta_session_id': "POSELEFT-" + str(uuid.uuid4())[:4] + "-" + str(uuid.uuid4())[:4],
        'exercise_date': time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/', methods=['GET', 'POST'])
def select_exercise():
    if request.method == 'POST':
        exercise = request.form.get('exercise')
        if exercise == 'left_curl':
            return redirect(url_for('left_curl_exercise'))
    return render_template('select_exercise.html')

@app.route('/left_curl', methods=['GET'])
def left_curl_exercise():
    return render_template('exercise.html', exercise='left_curl')

@app.route('/left_curl_feed', methods=['POST'])
def left_curl_feed():
    video_file = request.files.get('video')
    if video_file:
        return Response(generate_left_curl_frame(video_file), mimetype='image/jpeg')
    return '', 400

def save_image(img, patient_mrn, meta_session_id, count):
    if not os.path.exists('static/max_rom'):
        os.makedirs('static/max_rom')
    image_path = f'static/max_rom/{patient_mrn}_{meta_session_id}_{count}.jpg'
    cv2.imwrite(image_path, img)
    return image_path

def generate_left_curl_frame(video_file):
    global session_state

    detector = poseDetector()
    max_range_of_motion_percent = session_state['max_range_of_motion'] * 100

    data = video_file.read()
    np_arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return

    img = cv2.resize(img, (320, 240))  # Reduce resolution to speed up processing
    img = detector.findPose(img, False)
    lmList = detector.findPosition(img, False)
    elapsed_time = time.time() - session_state['start_time']

    if elapsed_time < session_state['countdown']:
        remaining_time = session_state['countdown'] - int(elapsed_time)
        cv2.putText(img, f'Starting in {remaining_time}s', (10, 20), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
        cv2.putText(img, f'Get in the ready position. Try to achieve {max_range_of_motion_percent}% ROM', (10, 40), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1)
    else:
        if session_state['count'] >= session_state['expected_count']:
            cv2.putText(img, 'Success! You reached the expected count!', (10, 20), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
            
            # Save the movements data for later retrieval
            movements_data = {
                "meta_session_id": session_state['meta_session_id'],
                "meta_patient_mrn": session_state['patient_mrn'],
                "meta_patient_name": session_state['patient_name'],
                "meta_exercise_type": session_state['exercise_type'],
                "meta_exercise_date": session_state['exercise_date'],
                "meta_max_range_of_motion": session_state['max_range_of_motion'],
                "meta_expected_count": session_state['expected_count'],
                "movements": session_state['movements']
            }
            np.save(f'./data/{session_state["meta_session_id"]}.npy', movements_data)
            
            reset_session_state()
            return redirect(url_for('select_exercise'))

        if len(lmList) != 0:
            elbow = detector.findAngle(img, 11, 13, 15)
            shoulder = detector.findAngle(img, 13, 11, 23)

            per = np.interp(elbow, (40, 160), (100, 0))

            if session_state['previous_angle'] is not None and elbow != session_state['previous_angle']:
                session_state['angle_change_count'] += 1
            session_state['previous_angle'] = elbow

            bar = np.interp(elbow, (40, 160), (50, 380))

            if shoulder < 40:
                session_state['form'] = 1

            if per > session_state['max_per']:
                session_state['max_per'] = per

            if session_state['form'] == 1:
                if per == 0 and session_state['max_per'] >= 50:
                    session_state['feedback'] = "now go UP"
                    session_state['feedback_color'] = (0, 255, 0)
                    if session_state['direction'] == 0:
                        movement_duration = time.time() - session_state['movement_start_time']
                        movement_speed = session_state['max_per'] / movement_duration
                        if session_state['movement_start_time']:
                            session_state['frames_for_gif'].append(img)
                            if len(session_state['frames_for_gif']) > 30:
                                session_state['frames_for_gif'].pop(0)
                            session_state['movements'].append({
                                "Count of movement": session_state['count'] + 1,
                                "Duration (s)": time.time() - session_state['movement_start_time'],
                                "Maxim ROM percentage achieved": session_state['max_per'],
                                "Movement speed (%/ms)": movement_speed,
                                "Stability - Angle change count": session_state['angle_change_count'],
                                "image_path": save_image(img, session_state['patient_mrn'], session_state['meta_session_id'], session_state['count'] + 1),
                            })
                        session_state['count'] += 1
                        session_state['direction'] = 1
                        session_state['max_per'] = 0
                        session_state['movement_start_time'] = time.time()
                elif per >= (session_state['max_range_of_motion'] * 100):
                    session_state['feedback'] = "Now go DOWN"
                    session_state['feedback_color'] = (0, 0, 255)
                    if session_state['direction'] == 1:
                        session_state['direction'] = 0

            if session_state['form'] == 1:
                cv2.rectangle(img, (320, 25), (330, 190), (0, 255, 0), 3)
                cv2.rectangle(img, (320, int(bar)), (330, 190), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, f'{int(per)}%', (240, 115), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), 2)

            percentage_complete = (session_state['count'] / session_state['expected_count']) * 100
            cv2.putText(img, f'{int(percentage_complete)}%', (10, 220), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (255, 0, 0), 2)

            reps_left = session_state['expected_count'] - session_state['count']
            cv2.putText(img, f'Reps left: {reps_left}', (10, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)

            cv2.putText(img, session_state['feedback'], (100, 20), cv2.FONT_HERSHEY_PLAIN, 2, session_state['feedback_color'], 2)

    cv2.putText(img, f'Patient: {session_state["patient_name"]}', (10, 230), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 0), 1)
    cv2.putText(img, f'MRN: {session_state["patient_mrn"]}', (10, 250), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)

    ret, jpeg = cv2.imencode('.jpg', img)

    return jpeg.tobytes()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5005)
