from exercises.left_curl import left_curl
# from exercises.right_curl import right_curl
# Import other exercises...

def process_exercise_frame(exercise_type, img, detector, patient_mrn, patient_name, meta_session_id, max_range_of_motion, expected_count, count, direction, max_per, movement_start_time, movements, angle_change_count, previous_angle, frames_for_gif):
    print('Recevied exercise type:', exercise_type) # Debugging
    try:
        if exercise_type == 'left_curl':
            return left_curl(img, detector, patient_mrn, patient_name, meta_session_id, max_range_of_motion, expected_count, count, direction, max_per, movement_start_time, movements, angle_change_count, previous_angle, frames_for_gif)
        # elif exercise_type == 'right_curl':
        #     return right_curl(img, detector, patient_mrn, patient_name, meta_session_id, max_range_of_motion, expected_count, count, direction, max_per, movement_start_time, movements, angle_change_count, previous_angle, frames_for_gif)
        # Add other exercises...
    except Exception as e:
        print('Error processing exercise frame:', e)
        return None
