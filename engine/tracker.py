import cv2
try:
    import mediapipe as mp
    try:
        # Try to access solutions (legacy API)
        mp_solutions = mp.solutions
        mp_hands = mp_solutions.hands
        mp_drawing = mp_solutions.drawing_utils
        HAS_MEDIAPIPE = True
    except AttributeError:
        print("Warning: mediapipe.solutions not found (likely Python 3.13+ incompatibility). Hand tracking disabled.")
        HAS_MEDIAPIPE = False
except ImportError:
    print("Warning: mediapipe not installed. Hand tracking disabled.")
    HAS_MEDIAPIPE = False

import threading
import time
import math

class HandTracker:
    def __init__(self, update_callback=None):
        self.output_callback = update_callback
        self.running = False
        self.thread = None
        
        if HAS_MEDIAPIPE:
            self.hands = mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )
            self.mp_drawing = mp_drawing
        else:
            self.hands = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _run_loop(self):
        cap = cv2.VideoCapture(0)
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # Convert BGR to RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hand_shape = "None"
            
            if HAS_MEDIAPIPE and self.hands:
                image.flags.writeable = False
                results = self.hands.process(image)
                image.flags.writeable = True
                
                # Convert back to BGR for drawing
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        self.mp_drawing.draw_landmarks(
                            image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        
                        # Basic Hand Shape Logic
                        landmark_list = []
                        for id, lm in enumerate(hand_landmarks.landmark):
                            h, w, c = image.shape
                            cx, cy = int(lm.x * w), int(lm.y * h)
                            landmark_list.append([id, cx, cy])

                        if landmark_list:
                             hand_shape = self._classify_hand_shape(landmark_list)
                # Use the processed image (with drawings)
                final_frame = image 
            else:
                # No mediapipe, just return original frame
                final_frame = frame
            
            # Send frame and data to UI callback
            if self.output_callback:
                self.output_callback(final_frame, hand_shape)
            
            # FPS limitation
            time.sleep(0.016)

        cap.release()

    def _classify_hand_shape(self, lm_list):
        """
        Simple heuristic for SASL hand shapes based on finger states.
        """
        # Finger tips: 8 (Index), 12 (Middle), 16 (Ring), 20 (Pinky)
        # Finger PIPs (knuckles): 6, 10, 14, 18
        
        fingers = []
        
        # Thumbs up logic (simplified)
        # Tip x > IP x (for right hand) - simplistic check
        fingers.append(1 if lm_list[4][1] > lm_list[3][1] else 0) 
        
        # 4 Fingers
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        
        for tip, pip in zip(tips, pips):
            if lm_list[tip][2] < lm_list[pip][2]: # Y-coordinate check (inverted)
                fingers.append(1)
            else:
                fingers.append(0)

        # Classify
        # Thumb, Index, Middle, Ring, Pinky
        if fingers == [0, 1, 1, 1, 1]:
            return "Flat Hand (B-Hand)"
        elif fingers == [0, 1, 1, 0, 0]:
            return "V-Shape"
        elif fingers == [0, 0, 0, 0, 0]: # Or [1, 0, 0, 0, 0] depending on thumb
            return "Fist (S-Hand)"
        elif fingers == [1, 0, 0, 0, 0]:
            return "Thumbs Up"
        elif fingers == [0, 1, 0, 0, 0]:
            return "Point (1-Hand)"
            
        return "Unknown"

if __name__ == "__main__":
    def print_result(frame, shape):
        print(f"Detected: {shape}")
        cv2.imshow('MediaPipe Hands', frame)
        if cv2.waitKey(5) & 0xFF == 27:
            pass

    tracker = HandTracker(update_callback=print_result)
    tracker.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        tracker.stop()
