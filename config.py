import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class EmailSettings:
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', os.getenv('SMTP_USERNAME'))
    RECIPIENTS = os.getenv('RECIPIENTS', '').split(',')
    
    @classmethod
    def validate(cls):
        if not all([cls.SMTP_USERNAME, cls.SMTP_PASSWORD, cls.RECIPIENTS]):
            raise ValueError("Missing email configuration in .env file")

email_settings = EmailSettings()