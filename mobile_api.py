from flask import Blueprint, jsonify, request
from typing import Dict, List
import jwt
import datetime
from config import DetectionConfig

mobile_api = Blueprint('mobile_api', __name__)

class MobileAPI:
    def __init__(self, config: DetectionConfig):
        self.config = config
        self.secret_key = "your_secret_key"  # Change this in production
        self.detection_history = []
        self.max_history = 100
        
    def add_detection(self, detection: Dict):
        """Add detection to history."""
        self.detection_history.append({
            **detection,
            'timestamp': datetime.datetime.now().isoformat()
        })
        if len(self.detection_history) > self.max_history:
            self.detection_history.pop(0)
            
    def get_detection_stats(self) -> Dict:
        """Get detection statistics."""
        stats = {}
        for det in self.detection_history:
            class_name = det['class']
            if class_name not in stats:
                stats[class_name] = 0
            stats[class_name] += 1
        return stats

# API Routes
@mobile_api.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    # Add your authentication logic here
    token = jwt.encode({
        'user': data.get('username'),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }, mobile_api.secret_key)
    return jsonify({'token': token})

@mobile_api.route('/api/detections', methods=['GET'])
def get_detections():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'No token provided'}), 401
        
    try:
        jwt.decode(token, mobile_api.secret_key, algorithms=['HS256'])
        return jsonify(mobile_api.detection_history)
    except:
        return jsonify({'error': 'Invalid token'}), 401

@mobile_api.route('/api/stats', methods=['GET'])
def get_stats():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'No token provided'}), 401
        
    try:
        jwt.decode(token, mobile_api.secret_key, algorithms=['HS256'])
        return jsonify(mobile_api.get_detection_stats())
    except:
        return jsonify({'error': 'Invalid token'}), 401

# Create global mobile API instance
mobile_api_instance = None

def init_mobile_api(config: DetectionConfig):
    """Initialize the mobile API."""
    global mobile_api_instance
    mobile_api_instance = MobileAPI(config) 