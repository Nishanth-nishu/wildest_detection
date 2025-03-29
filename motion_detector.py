import cv2
import numpy as np
from typing import Tuple, Optional
from config import DetectionConfig

class MotionDetector:
    def __init__(self, config: DetectionConfig):
        self.config = config
        self.prev_frame = None
        self.motion_threshold = config.motion_threshold
        
    def detect_motion(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        Detect motion in the current frame.
        Returns: (has_motion, motion_score)
        """
        if self.prev_frame is None:
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return False, 0.0
            
        # Convert current frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate frame difference
        frame_diff = cv2.absdiff(gray, self.prev_frame)
        
        # Apply threshold
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        
        # Calculate motion score (percentage of changed pixels)
        motion_score = np.sum(thresh > 0) / thresh.size
        
        # Update previous frame
        self.prev_frame = gray
        
        # Return motion status and score
        return motion_score > self.motion_threshold, motion_score
        
    def get_motion_region(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Get the region of motion in the frame.
        Returns: (x, y, width, height) or None if no significant motion
        """
        if self.prev_frame is None:
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return None
            
        # Convert current frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate frame difference
        frame_diff = cv2.absdiff(gray, self.prev_frame)
        
        # Apply threshold
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        # Find the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get bounding box
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Update previous frame
        self.prev_frame = gray
        
        return (x, y, w, h)
        
    def draw_motion_region(self, frame: np.ndarray, region: Tuple[int, int, int, int]) -> np.ndarray:
        """Draw the motion region on the frame."""
        x, y, w, h = region
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        return frame 