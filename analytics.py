import pandas as pd
import numpy as np
from typing import List, Dict
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from config import DetectionConfig
import logging

class Analytics:
    def __init__(self, config: DetectionConfig):
        self.config = config
        # Initialize empty DataFrame with proper columns and dtypes
        self.detections_df = pd.DataFrame({
            'timestamp': pd.Series(dtype='datetime64[ns]'),
            'class': pd.Series(dtype='str'),
            'confidence': pd.Series(dtype='float'),
            'x': pd.Series(dtype='float'),
            'y': pd.Series(dtype='float'),
            'width': pd.Series(dtype='float'),
            'height': pd.Series(dtype='float')
        })
        self.analytics_path = "analytics"
        os.makedirs(self.analytics_path, exist_ok=True)
        
    def add_detection(self, detection: Dict):
        """Add detection to analytics."""
        try:
            # Log the detection structure for debugging
            logging.debug(f"Detection structure: {detection}")
            
            # Extract detection data with proper error handling
            class_name = detection.get('name', 'unknown')  # YOLOv9 uses 'name' instead of 'class'
            confidence = detection.get('confidence', 0.0)
            bbox = detection.get('bbox', [0, 0, 0, 0])
            
            # Create a new row with proper timestamp
            new_row = pd.DataFrame([{
                'timestamp': pd.Timestamp.now(),
                'class': class_name,
                'confidence': float(confidence),
                'x': float(bbox[0]),
                'y': float(bbox[1]),
                'width': float(bbox[2]),
                'height': float(bbox[3])
            }])
            
            # Concatenate the new row to the DataFrame
            self.detections_df = pd.concat([self.detections_df, new_row], ignore_index=True)
            logging.debug(f"Added detection: {class_name} with confidence {confidence}")
            
        except Exception as e:
            logging.error(f"Error adding detection to analytics: {str(e)}")
            logging.error(f"Detection data: {detection}")
        
    def generate_daily_report(self):
        """Generate daily detection report."""
        if self.detections_df.empty:
            logging.info("No detections to generate daily report")
            return None
            
        today = datetime.now().date()
        daily_data = self.detections_df[
            self.detections_df['timestamp'].dt.date == today
        ]
        
        if daily_data.empty:
            logging.info("No detections for today")
            return None
            
        # Calculate statistics
        stats = {
            'total_detections': len(daily_data),
            'unique_classes': daily_data['class'].nunique(),
            'avg_confidence': daily_data['confidence'].mean(),
            'detections_by_class': daily_data['class'].value_counts().to_dict()
        }
        
        # Generate visualizations
        plt.figure(figsize=(10, 6))
        daily_data['class'].value_counts().plot(kind='bar')
        plt.title('Detections by Class')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{self.analytics_path}/daily_detections_{today}.png")
        plt.close()
        
        return stats
        
    def generate_weekly_report(self):
        """Generate weekly detection report."""
        if self.detections_df.empty:
            logging.info("No detections to generate weekly report")
            return None
            
        week_ago = datetime.now() - timedelta(days=7)
        weekly_data = self.detections_df[
            self.detections_df['timestamp'] >= week_ago
        ]
        
        if weekly_data.empty:
            logging.info("No detections in the last week")
            return None
            
        # Calculate statistics
        stats = {
            'total_detections': len(weekly_data),
            'unique_classes': weekly_data['class'].nunique(),
            'avg_confidence': weekly_data['confidence'].mean(),
            'detections_by_day': weekly_data.groupby(
                weekly_data['timestamp'].dt.date
            ).size().to_dict(),
            'detections_by_class': weekly_data['class'].value_counts().to_dict()
        }
        
        # Generate visualizations
        plt.figure(figsize=(12, 6))
        weekly_data.groupby(
            weekly_data['timestamp'].dt.date
        ).size().plot(kind='line', marker='o')
        plt.title('Detections Over Time')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{self.analytics_path}/weekly_trend.png")
        plt.close()
        
        return stats
        
    def get_realtime_stats(self) -> Dict:
        """Get real-time detection statistics."""
        if self.detections_df.empty:
            return {
                'detections_last_hour': 0,
                'detections_per_minute': 0,
                'top_classes': {},
                'avg_confidence': 0
            }
            
        last_hour = datetime.now() - timedelta(hours=1)
        recent_data = self.detections_df[
            self.detections_df['timestamp'] >= last_hour
        ]
        
        return {
            'detections_last_hour': len(recent_data),
            'detections_per_minute': len(recent_data) / 60,
            'top_classes': recent_data['class'].value_counts().head(3).to_dict(),
            'avg_confidence': recent_data['confidence'].mean()
        } 