from flask import Flask, render_template, Response, request, jsonify
import cv2
import threading
import time
import numpy as np
from detection import WildlifeDetector
from alert import EmailAlertSystem

app = Flask(__name__)

# Initialize components
detector = WildlifeDetector()
alert_system = EmailAlertSystem()

# Global variables with proper initialization
current_frame = None
frame_lock = threading.Lock()
user_email = None
current_source = None  # 'webcam' or 'video'
cap = None
video_path = None
stop_event = threading.Event()
detection_results = []

def cleanup_resources():
    """Safely release camera and other resources"""
    global cap
    stop_event.set()
    if cap is not None:
        cap.release()
        cap = None

def detection_loop():
    """Main detection thread that processes frames and detects wildlife"""
    global current_frame, cap, detection_results
    
    while not stop_event.is_set():
        try:
            # Frame acquisition based on source
            if current_source == 'webcam':
                if cap is None or not cap.isOpened():
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened():
                        # Handle webcam failure - create error frame
                        error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                        cv2.putText(error_frame, "Cannot access webcam", (50, 240), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        with frame_lock:
                            current_frame = error_frame
                        time.sleep(1)  # Avoid busy waiting
                        continue
                
                ret, frame = cap.read()
                if not ret:
                    continue
                    
            elif current_source == 'video' and video_path:
                if cap is None or not cap.isOpened():
                    cap = cv2.VideoCapture(video_path)
                    if not cap.isOpened():
                        # Handle video failure
                        error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                        cv2.putText(error_frame, "Cannot open video file", (50, 240), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        with frame_lock:
                            current_frame = error_frame
                        time.sleep(1)
                        continue
                
                ret, frame = cap.read()
                if not ret:
                    # Loop the video when it ends
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
            else:
                # No source selected or initialization frame
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "Select video source", (50, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Perform detection if source is active
            if current_source:
                detections = detector.detect(frame)
                
                # Check for new detections and send alerts if needed
                if detections and user_email:
                    for detection in detections:
                        if detection['confidence'] > 0.7:  # High confidence threshold for alerts
                            alert_system.send_alert(
                                user_email, 
                                f"Wildlife Detected: {detection['species']}",
                                frame
                            )
                
                # Update detection history - limit to most recent 20 entries
                for detection in detections:
                    detection_results.append({
                        'species': detection['species'],
                        'confidence': detection['confidence'],
                        'timestamp': time.time() * 1000  # Milliseconds timestamp
                    })
                detection_results = detection_results[-20:]
                
                # Draw bounding boxes and labels
                frame = detector.draw_detections(frame, detections)
            
            # Update shared frame with thread safety
            with frame_lock:
                current_frame = frame.copy()
                
            # Avoid high CPU usage
            time.sleep(0.03)  # ~30 FPS max
            
        except Exception as e:
            print(f"Error in detection loop: {e}")
            time.sleep(1)  # Prevent rapid error loops

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Stream video frames as MJPEG"""
    def generate():
        while True:
            with frame_lock:
                if current_frame is not None:
                    ret, buffer = cv2.imencode('.jpg', current_frame)
                    if not ret:
                        continue
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03)  # Control streaming rate
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_source', methods=['POST'])
def set_source():
    """Handle changing the video source"""
    global current_source, cap, video_path
    
    data = request.json
    new_source = data.get('source')
    
    # Clean up previous source
    if cap:
        cap.release()
        cap = None
    
    # Set new source
    if new_source in ['webcam', 'video']:
        current_source = new_source
        
        # Get video path if provided
        if new_source == 'video':
            video_path = data.get('video_path')
            
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid source type'})

@app.route('/set_email', methods=['POST'])
def set_email():
    """Save user email for alerts"""
    global user_email
    
    data = request.json
    email = data.get('email')
    
    if email and '@' in email:
        user_email = email
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid email format'})

@app.route('/detections', methods=['GET'])
def get_detections():
    """Return recent detections as JSON"""
    return jsonify({'detections': detection_results})

@app.errorhandler(Exception)
def handle_error(e):
    """Global error handler"""
    return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    try:
        # Start detection thread
        detection_thread = threading.Thread(target=detection_loop)
        detection_thread.daemon = True
        detection_thread.start()
        
        # Run the Flask app
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        # Ensure cleanup happens when app exits
        cleanup_resources()