from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
from typing import Optional
import logging
from config import DetectionConfig
from raspberry_utils import RaspberryPiMonitor
import time
import threading

# Create Flask app
app = Flask(__name__)

class WebInterface:
    def __init__(self, config: DetectionConfig):
        self.config = config
        self.monitor = RaspberryPiMonitor(config)
        self.current_frame = None
        self.detections = []
        self.system_info = {}
        self.logger = logging.getLogger(__name__)
        self.logger.info("WebInterface initialized successfully")
        self._stop_event = threading.Event()
        
    def update_frame(self, frame: np.ndarray, detections: list):
        """Update the current frame and detections."""
        try:
            self.current_frame = frame.copy()  # Make a copy to avoid reference issues
            self.detections = detections
            self.system_info = self.monitor.get_system_info()
            self.logger.debug(f"Updated frame with {len(detections)} detections")
        except Exception as e:
            self.logger.error(f"Error updating frame: {str(e)}")
        
    def generate_frames(self):
        """Generate frames for streaming."""
        while not self._stop_event.is_set():
            if self.current_frame is not None:
                try:
                    # Encode frame to JPEG
                    ret, buffer = cv2.imencode('.jpg', self.current_frame)
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                except Exception as e:
                    self.logger.error(f"Error generating frame: {str(e)}")
                    continue
            time.sleep(0.1)  # Add small delay to prevent CPU overuse
                
    def run(self):
        """Run the Flask web server."""
        try:
            self.logger.info(f"Starting web server on http://{self.config.web_host}:{self.config.web_port}")
            app.run(host=self.config.web_host, port=self.config.web_port, debug=False, use_reloader=False)
        except Exception as e:
            self.logger.error(f"Failed to start web server: {str(e)}")
            raise  # Re-raise the exception to handle it in the main thread
            
    def stop(self):
        """Stop the web interface."""
        self._stop_event.set()
        self.logger.info("Stopping web interface")

# Create global web interface instance
web_interface = None

def init_web_interface(config: DetectionConfig):
    """Initialize the web interface."""
    global web_interface
    try:
        if web_interface is None:
            web_interface = WebInterface(config)
            logging.info("Web interface initialized successfully")
            return True
        else:
            logging.warning("Web interface already initialized")
            return True
    except Exception as e:
        logging.error(f"Failed to initialize web interface: {str(e)}")
        return False

# Flask routes
@app.route('/')
def index():
    """Serve the main page."""
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error serving index page: {str(e)}")
        return str(e), 500

@app.route('/video_feed')
def video_feed():
    """Serve the video feed."""
    if web_interface is None:
        logging.error("Web interface not initialized when trying to serve video feed")
        return "Web interface not initialized", 500
    try:
        return Response(web_interface.generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        logging.error(f"Error serving video feed: {str(e)}")
        return str(e), 500

@app.route('/system_info')
def system_info():
    """Serve system information."""
    if web_interface is None:
        logging.error("Web interface not initialized when trying to serve system info")
        return "Web interface not initialized", 500
    try:
        return jsonify(web_interface.system_info)
    except Exception as e:
        logging.error(f"Error serving system info: {str(e)}")
        return str(e), 500

@app.route('/detections')
def detections():
    """Serve current detections."""
    if web_interface is None:
        logging.error("Web interface not initialized when trying to serve detections")
        return "Web interface not initialized", 500
    try:
        return jsonify(web_interface.detections)
    except Exception as e:
        logging.error(f"Error serving detections: {str(e)}")
        return str(e), 500 