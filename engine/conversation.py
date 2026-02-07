import speech_recognition as sr
import pyttsx3
import threading
from kivy.clock import Clock

class ConversationManager:
    def __init__(self, on_speech_recognized=None):
        self.mixer = None
        self.on_speech_recognized = on_speech_recognized
        
        # Initialize TTS
        self.tts_engine = pyttsx3.init()
        self._configure_voice()
        
        # Initialize Speech Recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.listen_thread = None

    def _configure_voice(self):
        """Try to set a South African English voice if available."""
        voices = self.tts_engine.getProperty('voices')
        sa_voice = None
        for voice in voices:
            if "english" in voice.name.lower() and ("south africa" in voice.name.lower() or "za" in voice.id.lower()):
                sa_voice = voice
                break
        
        if sa_voice:
            self.tts_engine.setProperty('voice', sa_voice.id)
            print(f"Using Voice: {sa_voice.name}")
        else:
            # Fallback to default
            print("South African voice not found, using default.")

    def speak(self, text):
        """Text-to-Speech (Sign-to-Voice)"""
        # Run in a separate thread to not block UI
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

    def start_listening(self):
        """Voice-to-Sign Listener"""
        if not self.is_listening:
            self.is_listening = True
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()

    def stop_listening(self):
        self.is_listening = False

    def _listen_loop(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print("Listening...")
            
            while self.is_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio)
                    print(f"Heard: {text}")
                    
                    if self.on_speech_recognized:
                        # Schedule callback on main thread
                        Clock.schedule_once(lambda dt: self.on_speech_recognized(text))
                        
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    print(f"Speech Error: {e}")
                    if not self.is_listening:
                        break

if __name__ == "__main__":
    def callback(text):
        print(f"Callback received: {text}")

    cm = ConversationManager(on_speech_recognized=callback)
    cm.speak("Hello from South Africa")
    # cm.start_listening() # Requires microphone
