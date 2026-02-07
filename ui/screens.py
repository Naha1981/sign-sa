from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import threading

# Import engines
try:
   from engine.tracker import HandTracker
   from engine.persistence import PersistenceManager
   from engine.conversation import ConversationManager
   from engine.grammar import SASLGrammarEngine
except ImportError as e:
   print("Import Error:", e)
   HandTracker = None
   PersistenceManager = None
   ConversationManager = None
   SASLGrammarEngine = None

class HomeScreen(Screen):
    pass

class LearnScreen(Screen):
    img = ObjectProperty(None)
    status_label = ObjectProperty(None)
    tracker = None

    def on_enter(self, *args):
        if HandTracker:
            self.tracker = HandTracker(update_callback=self.update_frame)
            self.tracker.start()
        else:
            print("HandTracker not available.")

    def on_leave(self, *args):
        if self.tracker:
            self.tracker.stop()

    def update_frame(self, frame, hand_shape):
        if not self.img: return
        
        # Convert frame
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        
        def update_ui(dt):
            self.img.texture = texture
            if self.status_label:
                self.status_label.text = f"Detected: {hand_shape}"
        
        Clock.schedule_once(update_ui)

class SOSScreen(Screen):
    def play_emergency_sign(self, sign_name):
        print(f"Playing emergency sign: {sign_name}")
        pass

class FeedbackScreen(Screen):
    sign_input = ObjectProperty(None)
    province_spinner = ObjectProperty(None)
    note_input = ObjectProperty(None)

    def submit_feedback(self):
        sign = self.sign_input.text
        province = self.province_spinner.text
        note = self.note_input.text
        
        if PersistenceManager:
            pm = PersistenceManager()
            pm.queue_feedback(sign, province, note)
            pm.close()
            print("Feedback submitted!")
            self.sign_input.text = ""
            self.note_input.text = ""

class ConversationScreen(Screen):
    chat_label = ObjectProperty(None)
    avatar_label = ObjectProperty(None)
    camera_image = ObjectProperty(None)
    mic_status_label = ObjectProperty(None)
    
    manager = None
    grammar = None
    tracker = None
    
    is_mic_on = False

    def on_enter(self, *args):
        # 1. Start Tracker (Sign-to-Voice Input)
        if HandTracker:
            self.tracker = HandTracker(update_callback=self.update_frame)
            self.tracker.start()

        # 2. Start Conversation Manager (Voice-to-Sign Input + TTS)
        if ConversationManager:
            self.manager = ConversationManager(on_speech_recognized=self.on_speech_recognized)
            
        # 3. Init Grammar
        if SASLGrammarEngine:
            self.grammar = SASLGrammarEngine()

    def on_leave(self, *args):
        if self.tracker:
            self.tracker.stop()
        if self.manager and self.is_mic_on:
            self.manager.stop_listening()
            self.is_mic_on = False

    def toggle_mic(self):
        if not self.manager: return
        
        if self.is_mic_on:
            self.manager.stop_listening()
            self.is_mic_on = False
            self.mic_status_label.text = "Mic: RED (OFF)"
            self.mic_status_label.color = (1, 0, 0, 1)
        else:
            try:
                self.manager.start_listening()
                self.is_mic_on = True
                self.mic_status_label.text = "Mic: GREEN (ON)"
                self.mic_status_label.color = (0, 1, 0, 1)
            except Exception as e:
                print(f"Mic Error: {e}")
                self.mic_status_label.text = "Mic Error"

    def on_speech_recognized(self, text):
        # Callback from ConversationManager (Threaded)
        print(f"Recognized: {text}")
        
        # Update Chat Log
        self.update_chat(f"Hearing: {text}")
        
        # Convert to Gloss
        if self.grammar:
            result = self.grammar.to_gloss(text)
            gloss = " ".join(result['gloss'])
            marker = result['facial_marker']
            
            # Simulate Avatar Playing
            self.update_avatar(gloss, marker)
            self.update_chat(f"Deaf: {gloss} ({marker})")

    def update_frame(self, frame, hand_shape):
        # Updates Camera Feed
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

        def ui_update(dt):
            if self.camera_image:
                self.camera_image.texture = texture
            
            # Simple Trigger: If "V-Shape" (Peace) is held -> Speak "Peace"
            # In real app, we need robustness (e.g. hold for 1 sec)
            if hand_shape == "V-Shape":
                # self.manager.speak("Peace") # Be careful not to spam TTS
                pass

        Clock.schedule_once(ui_update)

    def update_chat(self, message):
        def ui_update(dt):
            if self.chat_label:
                current_text = self.chat_label.text
                # Keep last 10 lines
                lines = current_text.split('\n')[-10:]
                lines.append(message)
                self.chat_label.text = "\n".join(lines)
        Clock.schedule_once(ui_update)

    def update_avatar(self, gloss, marker):
        def ui_update(dt):
            if self.avatar_label:
                self.avatar_label.text = f"[AVATAR]\nGloss: {gloss}\nFace: {marker}"
        Clock.schedule_once(ui_update)
