import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import logging
import time
from typing import List, Dict
from config import DetectionConfig

class AlertSystem:
    def __init__(self, config: DetectionConfig):
        self.config = config
        self.last_alert_time = 0
        self.alert_cooldown = 300  # 5 minutes between alerts
        self.logger = logging.getLogger(__name__)
        
    def send_email_alert(self, subject: str, body: str):
        """Send email alert if configured."""
        if not self.config.alert_email:
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.alert_email
            msg['To'] = self.config.alert_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Configure your email server settings here
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            # Add your email credentials here
            server.login(self.config.alert_email, "your_app_password")
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Email alert sent successfully")
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {str(e)}")
            
    def send_sms_alert(self, message: str):
        """Send SMS alert if configured."""
        if not self.config.alert_phone:
            return
            
        try:
            # Configure your SMS service here
            # This is a placeholder for actual SMS service integration
            self.logger.info(f"SMS alert would be sent: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send SMS alert: {str(e)}")
            
    def check_and_alert(self, detections: List[Dict]):
        """Check detections and send alerts if needed."""
        current_time = time.time()
        
        # Check if enough time has passed since last alert
        if current_time - self.last_alert_time < self.alert_cooldown:
            return
            
        # Check if any detections exceed confidence threshold
        high_confidence_detections = [
            det for det in detections 
            if det.get('confidence', 0) >= self.config.alert_confidence_threshold
        ]
        
        if high_confidence_detections:
            try:
                self._send_alert(high_confidence_detections)
                self.last_alert_time = current_time
            except Exception as e:
                self.logger.error(f"Failed to send alert: {str(e)}")
    
    def _send_alert(self, detections: List[Dict]):
        """Send alert with detection details."""
        alert_message = "Object Detection Alert!\n\n"
        alert_message += f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        alert_message += f"Location: {self.config.location}\n\n"
        alert_message += "Detected Objects:\n"
        
        for det in detections:
            class_name = det.get('name', 'unknown')  # Use 'name' instead of 'class'
            confidence = det.get('confidence', 0.0)
            alert_message += f"- {class_name} (Confidence: {confidence:.2f})\n"
        
        # Send email alert
        if self.config.enable_email_alerts:
            self._send_email_alert(alert_message)
        
        # Log alert
        self.logger.info(f"Alert sent: {alert_message}")
        
        # Send SMS alert
        self.send_sms_alert(alert_message) 