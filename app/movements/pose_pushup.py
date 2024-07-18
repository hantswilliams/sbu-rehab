import cv2
import mediapipe as mp
import numpy as np
import PoseModule as pm
import time
import uuid
import requests

def pushup(patient_mrn, patient_name, exercise_type, max_range_of_motion, expected_count):
    max_range_of_motion_percent = max_range_of_motion * 100
    cap = cv2.VideoCapture(0)
    detector = pm.poseDetector()
    count = 0
    direction = 0
    form = 0
    feedback = ""
    feedback_color = (0, 0, 0)
    max_per = 0
    countdown = 3
    start_time = time.time()
    movements = []
    angle_change_count = 0  # Count of angle changes
    previous_angle = None  # Previous angle to compare with
    movement_start_time = time.time()  # Initialize the movement start time
    exercise_date = time.strftime("%Y-%m-%d %H:%M:%S")
    meta_session_id = "POSEPUSHUP-" + str(uuid.uuid4())[:4] + "-" + str(uuid.uuid4())[:4]

    data = {
        "meta_session_id": meta_session_id,
        "meta_patient_mrn": patient_mrn,
        "meta_patient_name": patient_name,
        "meta_exercise_type": exercise_type,
        "meta_exercise_date": exercise_date,
        "meta_max_range_of_motion": max_range_of_motion,
        "meta_expected_count": expected_count
    }

    with detector.pose:
        while True:
            ret, img = cap.read()  # 640 x 480
            img = detector.findPose(img, False)
            lmList = detector.findPosition(img, False)
            elapsed_time = time.time() - start_time

            if elapsed_time < countdown:
                remaining_time = countdown - int(elapsed_time)
                cv2.putText(img, f'Starting in {remaining_time}s', (200, 200), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
                cv2.putText(img, f'Get in the ready position. Try to achieve {max_range_of_motion_percent}% ROM', (100, 250), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
            else:
                if count >= expected_count:
                    cv2.putText(img, 'Success! You reached the expected count!', (200, 200), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                    try:
                        response = requests.post('http://127.0.0.1:5007/set_completion')
                        print('Testing for response: ', response.json())
                    except Exception as e:
                        print(e)
                    cap.release()
                    cv2.destroyAllWindows()
                    break

                if len(lmList) != 0:
                    elbow = detector.findAngle(img, 11, 13, 15)
                    shoulder = detector.findAngle(img, 13, 11, 23)
                    hip = detector.findAngle(img, 11, 23, 25)

                    # Percentage of success of pushup
                    per = np.interp(elbow, (90, 160), (0, 100))

                    # Count the number of angle changes
                    if previous_angle is not None and elbow != previous_angle:
                        angle_change_count += 1
                    previous_angle = elbow

                    # Bar to show pushup progress
                    bar = np.interp(elbow, (90, 160), (380, 50))

                    # Check to ensure right form before starting the program
                    if elbow > 160 and shoulder > 40 and hip > 160:
                        form = 1

                    # Track the maximum percentage reached
                    if per > max_per:
                        max_per = per

                    # Check for full range of motion for the pushup
                    if form == 1:
                        if per == 0:
                            feedback = "now go UP"
                            feedback_color = (0, 255, 0)  # Green for UP
                            if direction == 0 and elbow <= 90 and hip > 160:
                                movement_duration = time.time() - movement_start_time
                                movement_speed = max_per / movement_duration  # Speed in percentage per second (%/s)
                                if movement_start_time:
                                    movements.append({
                                        "Count of movement": count + 1,
                                        "Duration (s)": time.time() - movement_start_time,  # Duration in seconds
                                        "Maxim ROM percentage achieved": max_per,
                                        "Movement speed (%/ms)": movement_speed,
                                        "Stability - Angle change count": angle_change_count,
                                    })
                                count += 1
                                direction = 1
                                max_per = 0  # Reset the max percentage after a complete pushup
                                movement_start_time = time.time()
                        elif per == 100:
                            feedback = "Now go DOWN"
                            feedback_color = (0, 0, 255)  # Red for DOWN
                            if direction == 1 and elbow > 160 and shoulder > 40 and hip > 160:
                                direction = 0

                    print(count)

                    # Draw Bar
                    if form == 1:
                        cv2.rectangle(img, (1080, 50), (1100, 380), (0, 255, 0), 3)
                        cv2.rectangle(img, (1080, int(bar)), (1100, 380), (0, 255, 0), cv2.FILLED)
                        cv2.putText(img, f'{int(per)}%', (950, 230), cv2.FONT_HERSHEY_PLAIN, 2,
                                    (255, 255, 0), 2)

                    # Counter (% complete of expected count)
                    percentage_complete = (count / expected_count) * 100
                    cv2.putText(img, f'{int(percentage_complete)}%', (25, 455), cv2.FONT_HERSHEY_COMPLEX_SMALL, 5,
                                (255, 0, 0), 5)

                    # Reps Left
                    reps_left = expected_count - count
                    cv2.putText(img, f'Reps left: {reps_left}', (100, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 255), 3)

                    # Feedback
                    cv2.putText(img, feedback, (500, 40), cv2.FONT_HERSHEY_PLAIN, 2, feedback_color, 2)

            # Display patient name and MRN on the bottom left-hand side
            cv2.putText(img, f'Patient: {patient_name}', (10, 670), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (0, 255, 0), 2)
            cv2.putText(img, f'MRN: {patient_mrn}', (10, 700), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

            # Convert the frame to JPEG format
            ret, jpeg = cv2.imencode('.jpg', img)

            # Yield the frame as a bytes-like object
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    data["movements"] = movements

    # Save the movements data for later retrieval
    np.save(f'./data/{meta_session_id}.npy', data)