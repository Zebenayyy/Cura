import cv2
import time
import numpy as np
import mediapipe as mp
import os
from tkinter import Tk, Label, Button
import requests
from flask import Flask, redirect, url_for, render_template

app=Flask(__name__)



url = 'https://www.nyckel.com/v1/functions/hair-types-identifier/invoke'
headers = {
    'Authorization': 'Bearer ' + 'eyJhbGciOiJSUzI1NiIsInR5cCI6ImF0K2p3dCJ9.eyJuYmYiOjE3Mjk0MTA2MjQsImV4cCI6MTcyOTQxNDIyNCwiaXNzIjoiaHR0cHM6Ly93d3cubnlja2VsLmNvbSIsImNsaWVudF9pZCI6InQ2NHY5dHUxcGFtYWU4ajIxOWIyNjdnMzlvZDR0ZHg5IiwianRpIjoiOUJBODA5QzRDN0I1MEUzODIwRTM4RDcwQUI5MkRDMjciLCJpYXQiOjE3Mjk0MTA2MjQsInNjb3BlIjpbImFwaSJdfQ.knhqu-OumvpKolmPGobdGhjpsEYTKXW_FY-ipaXM3-5rxZ0xKzKf_QFAVlOL_D8FXhGONH0jV9xJLUPQk2FGmVObcTP8jBg2zTlW2jUC7kUNawiSvRLUs8ZLJA1515g4rhNX0wJHyduDeL0oVlRdlX0OamJJvUCQ7B4w4H0PpSuWxyQ81liQz-SOQ7i0nfxkIm5cDU-ws_2dAmuEM1AQ_mXWbGKJpC6cb8wOrOQKGD2pseSwcERTsOBjjZom_wvN0D2FyE85QoIKsbsmc5DLNNPfN5v_1a1Eyd8F9fjGI8CYlykqkIeDVc6oAyGDpwANqkRIYcq7cNgtoAt2nYg8lg',
}


# Function to show a pop-up before starting the imaging process
def show_instructions():
    root = Tk()
    root.title("Instructions")

    # Set window size and position
    window_width = 400
    window_height = 200
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)
    root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

    # Create instruction label
    instruction = Label(root, text="Make sure your hair isn't tied up and follow\nthe picture on the left of the screen.", font=("Arial", 12), pady=20)
    instruction.pack()

    # Create OK button to start the imaging process
    def start_imaging():
        root.destroy()  # Close the pop-up window

    ok_button = Button(root, text="OK", command=start_imaging, padx=20, pady=10)
    ok_button.pack()

    root.mainloop()

# Load and resize the provided demonstration images
front_image = cv2.imread("C:/Users/kkw2jg/Desktop/GirlsHoohack/images/image for head rotation/FRONT.png")
right_image = cv2.imread("C:/Users/kkw2jg/Desktop/GirlsHoohack/images/image for head rotation/LEFT.png")
left_image = cv2.imread("C:/Users/kkw2jg/Desktop/GirlsHoohack/images/image for head rotation/RIGHT.png")

# Resize instruction images
def resize_image(image, target_height=480):
    height, width, _ = image.shape
    ratio = target_height / height
    new_width = int(width * ratio)
    return cv2.resize(image, (new_width, target_height))

front_image = resize_image(front_image)
left_image = resize_image(left_image)
right_image = resize_image(right_image)

# Initialize MediaPipe Face Mesh and drawing utilities
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

# 3D model points for head pose estimation
model_points = np.array([
    (0.0, 0.0, 0.0),           # Nose tip
    (0.0, -330.0, -65.0),       # Chin
    (-225.0, 170.0, -135.0),    # Left eye left corner
    (225.0, 170.0, -135.0),     # Right eye right corner
    (-150.0, -150.0, -125.0),   # Left mouth corner
    (150.0, -150.0, -125.0)     # Right mouth corner
])

# Function to determine face orientation
def determine_direction(rotation_vector):
    rvec_matrix = cv2.Rodrigues(rotation_vector)[0]
    proj_matrix = np.hstack((rvec_matrix, np.zeros((3, 1))))
    euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)[6]

    yaw = euler_angles[1][0]
    pitch = euler_angles[0][0]

    if pitch < -10:
        return "Up"
    elif pitch > 10:
        return "Down"
    elif yaw < -10:
        return "Left"
    elif yaw > 10:
        return "Right"
    else:
        return "Forward"

# Timer and capture function with side-by-side display
def capture_image(cap, instruction_image, orientation, camera_matrix, dist_coeffs, save_dir):
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0].landmark
            image_points = np.array([
                (face_landmarks[1].x * frame.shape[1], face_landmarks[1].y * frame.shape[0]),  # Nose tip
                (face_landmarks[152].x * frame.shape[1], face_landmarks[152].y * frame.shape[0]),  # Chin
                (face_landmarks[263].x * frame.shape[1], face_landmarks[263].y * frame.shape[0]),  # Right eye right corner
                (face_landmarks[33].x * frame.shape[1], face_landmarks[33].y * frame.shape[0]),  # Left eye left corner
                (face_landmarks[287].x * frame.shape[1], face_landmarks[287].y * frame.shape[0]),  # Right mouth corner
                (face_landmarks[57].x * frame.shape[1], face_landmarks[57].y * frame.shape[0])   # Left mouth corner
            ], dtype="double")

            success, rotation_vector, translation_vector = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs)
            
            face_orientation = determine_direction(rotation_vector)

            if face_orientation.lower() == orientation:
                print(f"Face detected in {orientation} orientation. Starting timer...")
                # 5 second countdown before capturing the image
                for i in range(5, 0, -1):
                    countdown_frame = frame.copy()
                    cv2.putText(countdown_frame, f"Capturing in {i}...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    combined_image = np.hstack((instruction_image, countdown_frame))
                    cv2.imshow('Instructions and Camera', combined_image)
                    cv2.waitKey(1000)  # Wait 1 second for each countdown step

                # Save the captured image to the specified folder
                image_path = os.path.join(save_dir, f'captured_{orientation}.png')
                cv2.imwrite(image_path, frame)
                print(f"Captured {orientation} image! Saved at: {image_path}")
                break

        combined_image = np.hstack((instruction_image, frame))
        cv2.imshow('Instructions and Camera', combined_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def main():
    # Path to save the captured images
    save_dir = "C:/Users/kkw2jg/Desktop/GirlsHoohack/Captured_picture"
    
    # Create the folder if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)  # Width
    cap.set(4, 480)  # Height

    focal_length = cap.get(3)
    center = (cap.get(3) / 2, cap.get(4) / 2)
    camera_matrix = np.array([[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]], dtype="double")
    dist_coeffs = np.zeros((4, 1))

    if not cap.isOpened():
        print("Could not open webcam")
        return

    # Show instructions before starting the imaging process
    show_instructions()

    try:
        capture_image(cap, front_image, "forward", camera_matrix, dist_coeffs, save_dir)
        capture_image(cap, left_image, "left", camera_matrix, dist_coeffs, save_dir)
        capture_image(cap, right_image, "right", camera_matrix, dist_coeffs, save_dir)
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
# Open the image file in binary mode
    file_path = "C:/Users/kkw2jg/Desktop/GirlsHoohack/Captured_picture/captured_forward.png"
    files = {'file': open(file_path, 'rb')}

# Make the POST request using multipart/form-data
    result = requests.post(url, headers=headers, files=files)
    print("Imaging process completed. Exiting...")
    print(result.text)

    # Exiting the program after all images are captured
    exit()
    


if __name__ == "__main__":
    main()
