import os
import cv2
import time
import logging
from pathlib import Path
from typing import Optional
import threading
import argparse

from yolov9 import YOLOv9
from config import DetectionConfig
from raspberry_utils import RaspberryPiMonitor
from motion_detector import MotionDetector
from web_interface import init_web_interface, web_interface
from alert_system import AlertSystem
from mobile_api import init_mobile_api, mobile_api_instance
from analytics import Analytics

def setup_logging(config: DetectionConfig):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"logs/{config.log_file}"),
            logging.StreamHandler()
        ]
    )

def get_detector(config: DetectionConfig) -> YOLOv9:
    """Initialize the YOLOv9 detector."""
    weights_path = config.weights_path
    classes_path = config.classes_path
    
    assert os.path.isfile(weights_path), f"There's no weight file with name {weights_path}"
    assert os.path.isfile(classes_path), f"There's no classes file with name {classes_path}"
    
    detector = YOLOv9(
        model_path=weights_path,
        class_mapping_path=classes_path,
        score_threshold=config.score_threshold,
        conf_thresold=config.conf_threshold,
        iou_threshold=config.iou_threshold,
        device=config.device
    )
    return detector

def process_video(config: DetectionConfig):
    """Process video stream with all features enabled."""
    logging.info("Starting video processing")
    
    # Initialize components
    detector = get_detector(config)
    monitor = RaspberryPiMonitor(config)
    motion_detector = MotionDetector(config)
    alert_system = AlertSystem(config)
    analytics = Analytics(config)
    
    # Initialize web interface if enabled
    web_thread = None
    if config.enable_web_interface:
        try:
            logging.info("Initializing web interface")
            if init_web_interface(config):
                if web_interface is not None:  # Check if web_interface was created
                    web_thread = threading.Thread(target=web_interface.run)
                    web_thread.daemon = True
                    web_thread.start()
                    logging.info(f"Web interface started on http://{config.web_host}:{config.web_port}")
                    # Wait a moment for the web interface to start
                    time.sleep(1)
                else:
                    logging.error("Web interface instance is None")
            else:
                logging.warning("Web interface initialization failed, continuing without web interface")
        except Exception as e:
            logging.error(f"Failed to initialize web interface: {str(e)}")
    
    # Open video capture
    if config.video_path:
        logging.info(f"Opening video file: {config.video_path}")
        cap = cv2.VideoCapture(config.video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {config.video_path}")
    else:
        logging.info("Opening webcam")
        cap = cv2.VideoCapture(0)  # Use default webcam (0)
        if not cap.isOpened():
            raise ValueError("Could not open webcam")
    
    # Set video properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logging.info(f"Video properties: {width}x{height} @ {fps}fps")
    if total_frames > 0:
        logging.info(f"Total frames: {total_frames}")
    
    # Initialize video writer if recording is enabled
    writer = None
    if config.enable_recording:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        recording_path = f"{config.recording_path}/recording_{int(time.time())}.mp4"
        writer = cv2.VideoWriter(recording_path, fourcc, 20.0, (width, height))
        logging.info(f"Recording enabled: {recording_path}")
    
    frame_idx = 0
    start_time = time.time()
    detection_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if config.video_path:
                    logging.info("End of video reached")
                else:
                    logging.error("Failed to grab frame from webcam")
                break
                
            frame_idx += 1
            
            # Perform object detection on every frame
            detections = detector.detect(frame)
            if detections:
                detection_count += 1
                logging.info(f"Frame {frame_idx}: Found {len(detections)} objects")
                detector.draw_detections(frame, detections=detections)
                
                # Update analytics
                for det in detections:
                    analytics.add_detection(det)
                    if config.enable_mobile_api and mobile_api_instance is not None:
                        mobile_api_instance.add_detection(det)
                
                # Check for alerts
                alert_system.check_and_alert(detections)
                
                # Update web interface if enabled
                if config.enable_web_interface and web_interface is not None:
                    web_interface.update_frame(frame, detections)
                
                # Record frame if enabled
                if config.enable_recording and writer:
                    writer.write(frame)
            
            # Calculate and display FPS
            elapsed_time = time.time() - start_time
            current_fps = frame_idx / elapsed_time
            cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Detections: {detection_count}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if config.video_path and total_frames > 0:
                progress = (frame_idx / total_frames) * 100
                cv2.putText(frame, f"Progress: {progress:.1f}%", (10, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display frame
            cv2.imshow("YOLOv9 Detection", frame)
            
            # Check for quit command
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logging.info("Quit command received")
                break
                
    finally:
        # Cleanup
        logging.info("Cleaning up resources")
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        
        # Stop web interface if it's running
        if config.enable_web_interface and web_interface is not None:
            web_interface.stop()
            if web_thread and web_thread.is_alive():
                web_thread.join(timeout=1)
            
        # Generate final reports
        logging.info("Generating final reports")
        analytics.generate_daily_report()
        analytics.generate_weekly_report()
        
        # Log final statistics
        total_time = time.time() - start_time
        logging.info(f"Processing completed:")
        logging.info(f"- Total frames processed: {frame_idx}")
        logging.info(f"- Total detections: {detection_count}")
        logging.info(f"- Average FPS: {frame_idx/total_time:.2f}")
        logging.info(f"- Total processing time: {total_time:.2f} seconds")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run YOLOv9 object detection")
    parser.add_argument("--video", type=str, help="Path to video file (optional)")
    parser.add_argument("--webcam", action="store_true", help="Use webcam instead of video file")
    args = parser.parse_args()
    
    # Create configuration with default settings
    config = DetectionConfig(
        weights_path="./weights/yolov9-t.onnx",
        classes_path="./weights/metadata.yaml",
        device="cpu",
        enable_web_interface=True,
        web_port=5000,
        web_host="0.0.0.0",  # Changed to 0.0.0.0 to allow all connections
        enable_mobile_api=True,
        mobile_api_port=5000,
        enable_analytics=True,
        enable_recording=True,
        enable_alerts=True,
        alert_email="maheshmahendrakar@kgr.ac.in",
        alert_confidence_threshold=0.5,
        location="Default Location"
    )
    
    # Override video path if provided
    if args.video:
        config.video_path = args.video
    elif args.webcam:
        config.video_path = None  # Will use webcam
    else:
        config.video_path = None  # Default to webcam
    
    # Setup logging
    setup_logging(config)
    
    # Process video/webcam
    process_video(config)
