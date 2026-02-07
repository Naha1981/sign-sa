from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import os
import cv2
import threading
import time

# --- Setup Paths ---
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

# --- Import Engines ---
try:
    from engine.tracker import HandTracker
    from engine.persistence import PersistenceManager
    from engine.conversation import ConversationManager
    from engine.grammar import SASLGrammarEngine
except ImportError as e:
    print(f"Import Warning: {e}")
    # Define dummy classes to allow UI to load even if engines fail
    class HandTracker:
        def __init__(self, update_callback=None): pass
        def start(self): pass
        def stop(self): pass
    class PersistenceManager:
        def __init__(self): pass
        def queue_feedback(self, a, b, c): pass
        def close(self): pass
    class ConversationManager:
        def __init__(self, on_speech_recognized=None): pass
        def start_listening(self): pass
        def stop_listening(self): pass
        def speak(self, text): pass
    class SASLGrammarEngine:
        def __init__(self): pass
        def to_gloss(self, text): return {"gloss": ["ERROR"], "facial_marker": "neutral"}

# --- Screen Definitions ---

class HomeScreen(Screen):
    pass

class LearnScreen(Screen):
    img = ObjectProperty(None)
    status_label = ObjectProperty(None)
    
    def on_enter(self, *args):
        try:
            self.tracker = HandTracker(update_callback=self.update_frame)
            self.tracker.start()
        except Exception as e:
            print(f"Tracker start error: {e}")

    def on_leave(self, *args):
        if hasattr(self, 'tracker'):
            self.tracker.stop()

    def update_frame(self, frame, hand_shape):
        try:
            # Flip & Convert for Kivy Texture
            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            
            def update_ui(dt):
                if self.img:
                    self.img.texture = texture
                if self.status_label:
                    self.status_label.text = f"Detected: {hand_shape}"
            
            Clock.schedule_once(update_ui)
        except Exception as e:
            print(f"Frame update error: {e}")

class SOSScreen(Screen):
    def play_emergency_sign(self, sign_name):
        print(f"Playing emergency sign: {sign_name}")

class FeedbackScreen(Screen):
    sign_input = ObjectProperty(None)
    province_spinner = ObjectProperty(None)
    note_input = ObjectProperty(None)

    def submit_feedback(self):
        try:
            pm = PersistenceManager()
            pm.queue_feedback(self.sign_input.text, self.province_spinner.text, self.note_input.text)
            pm.close()
            print("Feedback submitted!")
            self.sign_input.text = ""
            self.note_input.text = ""
        except Exception as e:
            print(f"Feedback error: {e}")

class ConversationScreen(Screen):
    # Kivy properties connected to KV IDs
    chat_log_text = StringProperty("Conversation Log:\n")
    mic_status = StringProperty("Mic: OFF")
    avatar_status = StringProperty("[Avatar Placeholder]\nWaiting for input...")
    img = ObjectProperty(None) 
    
    manager = None
    grammar = None
    tracker = None
    is_listening = False

    def on_enter(self, *args):
        # Initialize Backend Components
        try:
            self.tracker = HandTracker(update_callback=self.update_frame)
            self.tracker.start()
            
            self.manager = ConversationManager(on_speech_recognized=self.on_speech_callback)
            self.grammar = SASLGrammarEngine()
            
            self.chat_log_text += "[System] Conversation Mode Ready.\n"
        except Exception as e:
            self.chat_log_text += f"[System] Error initializing components: {e}\n"

    def on_leave(self, *args):
        if hasattr(self, 'tracker'):
            self.tracker.stop()
        if hasattr(self, 'manager') and self.is_listening:
            self.manager.stop_listening()

    def toggle_mic(self):
        if not self.manager: return
        
        if self.is_listening:
            self.manager.stop_listening()
            self.is_listening = False
            self.mic_status = "Mic: OFF"
        else:
            self.manager.start_listening()
            self.is_listening = True
            self.mic_status = "Mic: ON (Listening...)"

    def on_speech_callback(self, text):
        """Called from background thread when speech is recognized"""
        def process_speech(dt):
            self.chat_log_text += f"Hearing >> {text}\n"
            
            # Convert to Gloss
            if self.grammar:
                result = self.grammar.to_gloss(text)
                gloss = " ".join(result['gloss'])
                marker = result['facial_marker']
                
                # Update Avatar UI
                self.avatar_status = f"[AVATAR]\nGloss: {gloss}\nFace: {marker}"
                self.chat_log_text += f"Deaf << {gloss} ({marker})\n"
                
        Clock.schedule_once(process_speech)

    def update_frame(self, frame, hand_shape):
        # Update Camera Feed
        try:
            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

            def update_ui(dt):
                if self.img:
                    self.img.texture = texture
            
            Clock.schedule_once(update_ui)
        except Exception:
            pass

# --- Main App ---

class SASLTranslatorApp(App):
    def build(self):
        Window.size = (360, 640)
        
        # Load KV directly (fixing potential path issues)
        Builder.load_file('ui/main.kv')
        
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(LearnScreen(name='learn'))
        sm.add_widget(SOSScreen(name='sos'))
        sm.add_widget(FeedbackScreen(name='feedback'))
        sm.add_widget(ConversationScreen(name='conversation'))
        
        return sm

if __name__ == "__main__":
    SASLTranslatorApp().run()
