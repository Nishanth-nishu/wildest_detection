import os
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class DetectionConfig:
    # Model settings
    weights_path: str = "./weights/yolov9-t.onnx"
    classes_path: str = "./weights/metadata.yaml"
    device: str = "cpu"
    video_path: str = "0"  # Default to camera
    
    # Detection thresholds
    score_threshold: float = 0.1
    conf_threshold: float = 0.4
    iou_threshold: float = 0.4
    
    # Performance settings
    frame_skip: int = 2  # Process every nth frame
    max_fps: int = 30
    resolution: Tuple[int, int] = (640, 480)
    
    # Raspberry Pi specific
    enable_temp_monitoring: bool = True
    temp_threshold: float = 80.0  # Celsius
    power_save_mode: bool = True
    
    # Security features
    motion_detection: bool = True
    motion_threshold: float = 0.1
    enable_alerts: bool = True
    alert_email: Optional[str] = None
    alert_phone: Optional[str] = None
    alert_confidence_threshold: float = 0.5
    location: str = "Default Location"
    
    # Recording settings
    enable_recording: bool = True
    recording_path: str = "recordings"
    max_recording_duration: int = 3600  # seconds
    
    # Web interface
    enable_web_interface: bool = True
    web_port: int = 5000
    web_host: str = "0.0.0.0"
    
    # Mobile API
    enable_mobile_api: bool = True
    mobile_api_port: int = 5000
    mobile_api_host: str = "0.0.0.0"
    
    # Analytics
    enable_analytics: bool = True
    analytics_path: str = "analytics"
    analytics_retention_days: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "detection.log"
    
    def __post_init__(self):
        # Create necessary directories
        os.makedirs(self.recording_path, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs(self.analytics_path, exist_ok=True) 