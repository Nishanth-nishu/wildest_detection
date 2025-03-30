import smtplib
import os
import time
import logging
import cv2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.utils import formatdate
from pathlib import Path
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wildlife_alert')

class EmailAlertSystem:
    """
    System for sending email alerts when wildlife is detected.
    Includes rate limiting, image attachments, and error handling.
    Compatible with config.py EmailSettings.
    """
    
    def __init__(self):
        try:
            # Try to import from config
            from config import email_settings
            
            self.smtp_server = email_settings.SMTP_SERVER
            self.smtp_port = email_settings.SMTP_PORT
            self.sender_email = email_settings.SENDER_EMAIL
            self.sender_password = email_settings.SMTP_PASSWORD
            self.default_recipients = email_settings.RECIPIENTS
            
            logger.info("Using email configuration from config.py")
        except (ImportError, AttributeError):
            # Fall back to environment variables if config import fails
            from dotenv import load_dotenv
            load_dotenv()
            
            self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            self.smtp_port = int(os.getenv('SMTP_PORT', 587))
            self.sender_email = os.getenv('SENDER_EMAIL', os.getenv('SMTP_USERNAME'))
            self.sender_password = os.getenv('SMTP_PASSWORD')
            self.default_recipients = os.getenv('RECIPIENTS', '').split(',')
            
            logger.info("Using email configuration from environment variables")
        
        # Alert configuration
        self.rate_limit_seconds = int(os.getenv('ALERT_RATE_LIMIT_SECONDS', 300))  # 5 minutes default
        self.last_alerts = {}  # Track last alert time per email/species combination
        self.alert_lock = threading.Lock()  # Thread safety for alert tracking
        
        # Create directory for temporary image storage
        self.temp_dir = Path("temp_images")
        self.temp_dir.mkdir(exist_ok=True)
        
        # Verify configuration
        self._verify_config()

    def _verify_config(self):
        """Verify that required email configuration is available"""
        missing = []
        if not self.sender_email:
            missing.append("SENDER_EMAIL/SMTP_USERNAME")
        if not self.sender_password:
            missing.append("SMTP_PASSWORD")
            
        if missing:
            logger.warning(f"Email alert configuration incomplete. Missing: {', '.join(missing)}")
            logger.warning("Email alerts will be logged but not sent until configuration is complete")
    
    def _can_send_alert(self, email, species):
        """
        Check if we should send an alert based on rate limiting
        Returns True if alert should be sent, False otherwise
        """
        with self.alert_lock:
            # Unique key for this email/species combination
            key = f"{email}:{species}"
            current_time = time.time()
            
            # Check if we've sent an alert recently
            if key in self.last_alerts:
                time_diff = current_time - self.last_alerts[key]
                if time_diff < self.rate_limit_seconds:
                    # Too soon for another alert
                    return False
            
            # Update last alert time and allow sending
            self.last_alerts[key] = current_time
            return True
    
    def _save_temp_image(self, image):
        """Save detection image to a temporary file and return the path"""
        if image is None:
            return None
            
        timestamp = int(time.time())
        image_path = self.temp_dir / f"detection_{timestamp}.jpg"
        
        try:
            cv2.imwrite(str(image_path), image)
            return image_path
        except Exception as e:
            logger.error(f"Failed to save detection image: {e}")
            return None
    
    def _cleanup_temp_images(self):
        """Delete old temporary images to prevent disk space issues"""
        try:
            current_time = time.time()
            for image_file in self.temp_dir.glob("*.jpg"):
                # Delete images older than 1 hour
                if current_time - image_file.stat().st_mtime > 3600:
                    image_file.unlink()
        except Exception as e:
            logger.error(f"Error cleaning up temporary images: {e}")
    
    def _send_single_alert(self, email, subject, image, species, confidence, location):
        """Helper method to send an alert to a single recipient"""
        # Basic validation
        if not email or '@' not in email:
            logger.error(f"Invalid email address: {email}")
            return False
            
        # Default species name for rate limiting if not provided
        species_name = species or "wildlife"
        
        # Check rate limiting
        if not self._can_send_alert(email, species_name):
            logger.info(f"Rate limited alert for {species_name} to {email}")
            return False
            
        # Check if email configuration is complete
        if not self.sender_email or not self.sender_password:
            logger.info(f"Would send alert to {email} about {species_name}, but email config is incomplete")
            return False
            
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = email
            msg['Subject'] = subject
            msg['Date'] = formatdate(localtime=True)
            
            # Create email body
            body = ["Wildlife Detection Alert!"]
            
            if species:
                body.append(f"Species: {species}")
            if confidence is not None:
                body.append(f"Confidence: {confidence:.1%}")
            if location:
                body.append(f"Location: {location}")
                
            body.append("\nThis is an automated alert from your wildlife monitoring system.")
            
            # Add body to email
            msg.attach(MIMEText("\n".join(body), 'plain'))
            
            # Add image if provided
            if image is not None:
                # Save image to temporary file
                image_path = self._save_temp_image(image)
                
                if image_path and image_path.exists():
                    with open(image_path, 'rb') as img_file:
                        img_data = img_file.read()
                        
                    image_attachment = MIMEImage(img_data)
                    image_attachment.add_header('Content-Disposition', 'attachment', 
                                               filename=f'wildlife_detection.jpg')
                    msg.attach(image_attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            logger.info(f"Alert sent to {email} for {species_name}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check email credentials.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
            
    def send_alert(self, email=None, subject="Wildlife Detected", image=None, species=None, confidence=None, location=None):
        """
        Send an email alert with optional image attachment when wildlife is detected
        
        Args:
            email (str, optional): Recipient email address, uses default recipients if None
            subject (str): Email subject
            image (numpy.ndarray, optional): Image frame with the detection
            species (str, optional): Detected species name
            confidence (float, optional): Detection confidence (0-1)
            location (str, optional): Location information
            
        Returns:
            bool: True if alert was sent successfully, False otherwise
        """
        # Use provided email or default recipients
        if email:
            recipients = [email]
        else:
            recipients = [r for r in self.default_recipients if r]  # Filter out empty strings
        
        if not recipients:
            logger.warning("No recipients specified and no default recipients configured")
            return False
        
        # Send to all recipients
        success = True
        for recipient in recipients:
            if not self._send_single_alert(recipient, subject, image, species, confidence, location):
                success = False
        
        # Clean up old temporary images regardless of success
        self._cleanup_temp_images()
            
        return success