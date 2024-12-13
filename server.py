from flask import Flask, render_template, Response
import os
import cv2
import requests

camera = cv2.VideoCapture(0)  

url = 'https://www.nyckel.com/v1/functions/hair-types-identifier/invoke'
headers = {
    'Authorization': 'Bearer ' + 'eyJhbGciOiJSUzI1NiIsInR5cCI6ImF0K2p3dCJ9.eyJuYmYiOjE3Mjk0MTA2MjQsImV4cCI6MTcyOTQxNDIyNCwiaXNzIjoiaHR0cHM6Ly93d3cubnlja2VsLmNvbSIsImNsaWVudF9pZCI6InQ2NHY5dHUxcGFtYWU4ajIxOWIyNjdnMzlvZDR0ZHg5IiwianRpIjoiOUJBODA5QzRDN0I1MEUzODIwRTM4RDcwQUI5MkRDMjciLCJpYXQiOjE3Mjk0MTA2MjQsInNjb3BlIjpbImFwaSJdfQ.knhqu-OumvpKolmPGobdGhjpsEYTKXW_FY-ipaXM3-5rxZ0xKzKf_QFAVlOL_D8FXhGONH0jV9xJLUPQk2FGmVObcTP8jBg2zTlW2jUC7kUNawiSvRLUs8ZLJA1515g4rhNX0wJHyduDeL0oVlRdlX0OamJJvUCQ7B4w4H0PpSuWxyQ81liQz-SOQ7i0nfxkIm5cDU-ws_2dAmuEM1AQ_mXWbGKJpC6cb8wOrOQKGD2pseSwcERTsOBjjZom_wvN0D2FyE85QoIKsbsmc5DLNNPfN5v_1a1Eyd8F9fjGI8CYlykqkIeDVc6oAyGDpwANqkRIYcq7cNgtoAt2nYg8lg',
}

def gen_frames():
    while True:
        success, frame = camera.read()  # Capture frame-by-frame
        if not success:
            break
        else:
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_image', methods=['POST'])
def capture_image():
    success, frame = camera.read()
    if success:
        # Save the frame as an image file (you can adjust the path)
        img_path = os.path.join('static', 'captured_image.jpg')
        cv2.imwrite(img_path, frame)
        
        files = {'file': open(img_path, 'rb')}

    # Make the POST request using multipart/form-data
        result = requests.post(url, headers=headers, files=files)
        print("Imaging process completed. Exiting...")
        print(result.text)


        return {'status': 'success', 'image_path': img_path, "results": result.text}
    else:
        return {'status': 'error', 'message': 'Failed to capture image'}, 500

@app.route('/app')
def main():
    # os.system("python app.py")
    return "ok"

# @app.route("/analyze_hair", methods=['POST'])
# def analyze():
#     # files = request.data()
#     url = 'https://www.nyckel.com/v1/functions/hair-types-identifier/invoke'
#     headers = {
#     'Authorization': 'Bearer ' + 'eyJhbGciOiJSUzI1NiIsInR5cCI6ImF0K2p3dCJ9.eyJuYmYiOjE3Mjk0MTA2MjQsImV4cCI6MTcyOTQxNDIyNCwiaXNzIjoiaHR0cHM6Ly93d3cubnlja2VsLmNvbSIsImNsaWVudF9pZCI6InQ2NHY5dHUxcGFtYWU4ajIxOWIyNjdnMzlvZDR0ZHg5IiwianRpIjoiOUJBODA5QzRDN0I1MEUzODIwRTM4RDcwQUI5MkRDMjciLCJpYXQiOjE3Mjk0MTA2MjQsInNjb3BlIjpbImFwaSJdfQ.knhqu-OumvpKolmPGobdGhjpsEYTKXW_FY-ipaXM3-5rxZ0xKzKf_QFAVlOL_D8FXhGONH0jV9xJLUPQk2FGmVObcTP8jBg2zTlW2jUC7kUNawiSvRLUs8ZLJA1515g4rhNX0wJHyduDeL0oVlRdlX0OamJJvUCQ7B4w4H0PpSuWxyQ81liQz-SOQ7i0nfxkIm5cDU-ws_2dAmuEM1AQ_mXWbGKJpC6cb8wOrOQKGD2pseSwcERTsOBjjZom_wvN0D2FyE85QoIKsbsmc5DLNNPfN5v_1a1Eyd8F9fjGI8CYlykqkIeDVc6oAyGDpwANqkRIYcq7cNgtoAt2nYg8lg',
#     }
#     files = {'file': open(file_path, 'rb')}

#     # Make the POST request using multipart/form-data
#     result = requests.post(url, headers=headers, files=files)
#     print("Imaging process completed. Exiting...")
#     print(result.text)

app.run(debug=True)

