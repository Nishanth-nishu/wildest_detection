import cv2
import numpy as np

class WildlifeDetector:
    def __init__(self, weights_path="weights/yolov9-t.onnx"):
        self.net = cv2.dnn.readNet(weights_path)
        self.input_size = 640
        self.conf_threshold = 0.5
        self.classes = self._load_classes("weights/metadata.yaml")

    def _load_classes(self, path):
        with open(path, 'r') as f:
            return [line.strip() for line in f.readlines()]

    def detect(self, frame):
        # Preprocess
        blob = cv2.dnn.blobFromImage(
            frame, 
            1/255.0, 
            (self.input_size, self.input_size), 
            swapRB=True, 
            crop=False
        )
        
        self.net.setInput(blob)
        
        try:
            # Get output layers
            output_layers = self.net.getUnconnectedOutLayersNames()
            outputs = self.net.forward(output_layers)
            
            detections = []
            for output in outputs:
                # Reshape to 2D array [num_detections, (x,y,w,h,conf,class_conf...)]
                output = output.reshape(output.shape[1], -1)
                
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores[:len(self.classes)])  # Only consider valid classes
                    confidence = scores[class_id]
                    
                    if confidence > self.conf_threshold:
                        detections.append({
                            'species': self.classes[class_id],
                            'confidence': float(confidence),
                            'box': detection[:4]  # x, y, w, h
                        })
            
            return detections
            
        except Exception as e:
            print(f"Detection error: {e}")
            return []

    def draw_detections(self, frame, detections):
        h, w = frame.shape[:2]
        for det in detections:
            x, y, w, h = det['box']
            # Convert normalized coordinates to pixel values
            x = int(x * w)
            y = int(y * h)
            width = int(w * w)
            height = int(h * h)
            
            cv2.rectangle(frame, (x, y), (x+width, y+height), (0, 255, 0), 2)
            cv2.putText(frame, 
                       f"{det['species']} {det['confidence']:.1%}", 
                       (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return frame