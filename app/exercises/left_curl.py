import cv2
import mediapipe as mp
import numpy as np
import PoseModule as pm
import time
import uuid
import os

def save_image(img, patient_mrn, meta_session_id, count):
    if not os.path.exists('static/max_rom'):
        os.makedirs('static/max_rom')
    
    image_path = f'static/max_rom/{patient_mrn}_{meta_session_id}_{count}.jpg'
    cv2.imwrite(image_path, img)
    
    return image_path

def left_curl(img, detector, patient_mrn, patient_name, meta_session_id, max_range_of_motion, expected_count, count, direction, max_per, movement_start_time, movements, angle_change_count, previous_angle, frames_for_gif):
    max_range_of_motion_percent = max_range_of_motion * 100
    feedback = ""
    feedback_color = (0, 0, 0)

    img = detector.findPose(img, False)
    lmList = detector.findPosition(img, False)

    if len(lmList) != 0:
        elbow = detector.findAngle(img, 11, 13, 15)
        shoulder = detector.findAngle(img, 13, 11, 23)

        per = np.interp(elbow, (40, 160), (100, 0))

        if previous_angle is not None and elbow != previous_angle:
            angle_change_count += 1
        previous_angle = elbow

        bar = np.interp(elbow, (40, 160), (50, 380))

        if shoulder < 40:
            form = 1

        if per > max_per:
            max_per = per

        if form == 1:
            if per == 0 and max_per >= 50:
                feedback = "now go UP"
                feedback_color = (0, 255, 0)
                if direction == 0:
                    movement_duration = time.time() - movement_start_time
                    movement_speed = max_per / movement_duration
                    if movement_start_time:
                        frames_for_gif.append(img)
                        if len(frames_for_gif) > 30:
                            frames_for_gif.pop(0)
                        movements.append({
                            "Count of movement": count + 1,
                            "Duration (s)": time.time() - movement_start_time,
                            "Maxim ROM percentage achieved": max_per,
                            "Movement speed (%/ms)": movement_speed,
                            "Stability - Angle change count": angle_change_count,
                            "image_path": save_image(img, patient_mrn, meta_session_id, count + 1),
                        })
                    count += 1
                    direction = 1
                    max_per = 0
                    movement_start_time = time.time()
            elif per >= (max_range_of_motion * 100):
                feedback = "Now go DOWN"
                feedback_color = (0, 0, 255)
                if direction == 1:
                    direction = 0

        if form == 1:
            cv2.rectangle(img, (1080, 50), (1100, 380), (0, 255, 0), 3)
            cv2.rectangle(img, (1080, int(bar)), (1100, 380), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, f'{int(per)}%', (950, 230), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), 2)

        percentage_complete = (count / expected_count) * 100
        cv2.putText(img, f'{int(percentage_complete)}%', (25, 455), cv2.FONT_HERSHEY_COMPLEX_SMALL, 5, (255, 0, 0), 5)
        reps_left = expected_count - count
        cv2.putText(img, f'Reps left: {reps_left}', (100, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 255), 3)
        cv2.putText(img, feedback, (500, 40), cv2.FONT_HERSHEY_PLAIN, 2, feedback_color, 2)

    ret, jpeg = cv2.imencode('.jpg', img)
    return jpeg.tobytes(), count, direction, max_per, movement_start_time, movements, angle_change_count, previous_angle, frames_for_gif
