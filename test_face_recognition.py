import cv2
import os
import serial
import time
import requests
import pyttsx3
from datetime import datetime
from deepface import DeepFace
from flask import Flask, render_template_string
import threading

# ==================== CONFIGURATION ====================
class Config:
    # ESP32 Connection
    ESP32_PORT = 'COM5'  # Change to your ESP32 port (Windows: COM3, Linux: /dev/ttyUSB0, Mac: /dev/cu.usbserial)
    BAUD_RATE = 115200
    
    # Directories
    FACES_DB = 'registered_faces/'
    ATTENDANCE_FILE = 'attendance.csv'
    CAPTURES_FOLDER = 'captured_faces/'
    
    # DeepFace Settingsq
    MODEL_NAME = 'Facenet'  # Options: VGG-Face, Facenet, OpenFace, DeepFace
    DISTANCE_METRIC = 'cosine'  # Options: cosine, euclidean
    CONFIDENCE_THRESHOLD = 60  # Minimum confidence to recognize (0-100)
    
    # Recognition Settings
    RECOGNITION_COOLDOWN = 2  # Seconds between auto-recognition
    
    # Telegram Bot (Optional)
    TELEGRAM_ENABLED = True  # Set True to enable
    TELEGRAM_BOT_TOKEN = '8493226095:AAHAdQ_Yz8aP-uDmk4SrC2AX6dtqfOSputA'  # Get from @BotFather
    TELEGRAM_CHAT_ID = '6707051159'
    
    # Location
    LOCATION = "Main Building - Gate A"
    
    # Voice Announcements
    VOICE_ENABLED = True
    VOICE_RATE = 150  # Speech rate

# Create necessary folders
os.makedirs(Config.FACES_DB, exist_ok=True)
os.makedirs(Config.CAPTURES_FOLDER, exist_ok=True)

# ==================== ESP32 CONNECTION ====================
class ESP32Controller:
    def __init__(self):
        self.serial = None
        self.connect()
    
    def connect(self):
        try:
            self.serial = serial.Serial(Config.ESP32_PORT, Config.BAUD_RATE, timeout=1)
            time.sleep(2)  # Wait for ESP32 to initialize
            print(f"✅ Connected to ESP32 on {Config.ESP32_PORT}")
            return True
        except Exception as e:
            print(f"❌ Error connecting to ESP32: {e}")
            print(f"💡 Make sure ESP32 is connected to {Config.ESP32_PORT}")
            return False
    
    def send_command(self, command):
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(f"{command}\n".encode())
                return True
            except Exception as e:
                print(f"⚠️ Error sending command: {e}")
                return False
        return False
    
    def close(self):
        if self.serial and self.serial.is_open:
            self.serial.close()

# ==================== VOICE ENGINE ====================
class VoiceAnnouncer:
    def __init__(self):
        self.enabled = Config.VOICE_ENABLED
        if self.enabled:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', Config.VOICE_RATE)
                print("✅ Voice engine initialized")
            except Exception as e:
                print(f"⚠️ Voice engine failed: {e}")
                self.enabled = False
    
    def speak(self, text):
        if self.enabled:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except:
                pass

# ==================== TELEGRAM NOTIFICATIONS ====================
class TelegramNotifier:
    def __init__(self):
        self.enabled = Config.TELEGRAM_ENABLED
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
    
    def send_photo(self, name, image_path):
        if not self.enabled:
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.chat_id,
                    'caption': f"✅ {name} arrived at {datetime.now().strftime('%H:%M:%S')}\n📍 {Config.LOCATION}"
                }
                response = requests.post(url, files=files, data=data, timeout=5)
                
            if response.status_code == 200:
                print(f"📱 Telegram notification sent for {name}")
            else:
                print(f"⚠️ Telegram failed: {response.text}")
        except Exception as e:
            print(f"⚠️ Telegram error: {e}")
    
    def send_message(self, message):
        if not self.enabled:
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {'chat_id': self.chat_id, 'text': message}
            requests.post(url, data=data, timeout=5)
        except:
            pass

# ==================== WEB DASHBOARD ====================
class WebDashboard:
    def __init__(self):
        self.app = Flask(__name__)
        self.attendance_data = []
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/')
        def dashboard():
            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>SmartAttend AI Dashboard</title>
                <meta http-equiv="refresh" content="5">
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                        color: white; 
                        padding: 20px;
                        min-height: 100vh;
                    }
                    h1 { color: #00d9ff; text-align: center; margin-bottom: 10px; }
                    .subtitle { text-align: center; color: #888; margin-bottom: 30px; }
                    .stats { 
                        display: grid; 
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                        gap: 20px; 
                        margin-bottom: 30px; 
                    }
                    .stat-box { 
                        background: #0f3460; 
                        padding: 25px; 
                        border-radius: 12px; 
                        text-align: center;
                        border: 1px solid #00d9ff;
                    }
                    .stat-number { font-size: 48px; color: #00d9ff; font-weight: bold; }
                    .stat-label { margin-top: 10px; color: #ccc; font-size: 14px; }
                    table { 
                        width: 100%; 
                        border-collapse: collapse; 
                        background: #0f3460; 
                        border-radius: 12px; 
                        overflow: hidden;
                    }
                    th { 
                        background: #00d9ff; 
                        color: #000; 
                        padding: 15px; 
                        text-align: left; 
                        font-weight: bold;
                    }
                    td { padding: 12px 15px; border-bottom: 1px solid #333; }
                    tr:hover { background: rgba(0, 217, 255, 0.1); }
                    .status { 
                        display: inline-block; 
                        padding: 5px 10px; 
                        border-radius: 5px; 
                        background: #28a745; 
                        color: white; 
                        font-size: 12px;
                    }
                </style>
            </head>
            <body>
                <h1>📊 SmartAttend AI Dashboard</h1>
                <p class="subtitle">Real-time Attendance Monitoring System</p>
                <p class="subtitle">📍 Location: ''' + Config.LOCATION + '''</p>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number">''' + str(len(self.attendance_data)) + '''</div>
                        <div class="stat-label">Total Present Today</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">''' + datetime.now().strftime('%H:%M') + '''</div>
                        <div class="stat-label">Current Time</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">''' + datetime.now().strftime('%d') + '''</div>
                        <div class="stat-label">''' + datetime.now().strftime('%B %Y') + '''</div>
                    </div>
                </div>
                
                <h2 style="color: #00d9ff; margin: 20px 0;">Recent Attendance</h2>
                <table>
                    <tr>
                        <th>#</th>
                        <th>Name</th>
                        <th>Time</th>
                        <th>Location</th>
                        <th>Status</th>
                    </tr>
                    ''' + ''.join([f'''<tr>
                        <td>{i+1}</td>
                        <td>{d["name"]}</td>
                        <td>{d["time"]}</td>
                        <td>{d["location"]}</td>
                        <td><span class="status">Present</span></td>
                    </tr>''' for i, d in enumerate(self.attendance_data[-10:][::-1])]) + '''
                </table>
            </body>
            </html>
            '''
            return html
    
    def add_attendance(self, name, time_str):
        self.attendance_data.append({
            "name": name,
            "time": time_str,
            "location": Config.LOCATION
        })
    
    def start(self):
        def run():
            self.app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        print("✅ Web dashboard started at http://localhost:5000")

# ==================== ATTENDANCE MANAGER ====================
class AttendanceManager:
    def __init__(self, esp32, voice, telegram, dashboard):
        self.esp32 = esp32
        self.voice = voice
        self.telegram = telegram
        self.dashboard = dashboard
        self.marked_today = set()
        self.initialize_csv()
    
    def initialize_csv(self):
        if not os.path.exists(Config.ATTENDANCE_FILE):
            with open(Config.ATTENDANCE_FILE, 'w') as f:
                f.write("Name,Date,Time,Location\n")
    
    def mark_attendance(self, name, frame):
        if name in self.marked_today:
            print(f"⚠️ {name} already marked present today!")
            self.esp32.send_command(f"ALREADY:{name}")
            self.voice.speak(f"{name} already marked present")
            return False
        
        # Save timestamp
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        # Save captured photo
        photo_filename = os.path.join(
            Config.CAPTURES_FOLDER,
            f"{name}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
        )
        cv2.imwrite(photo_filename, frame)
        
        # Write to CSV
        with open(Config.ATTENDANCE_FILE, 'a') as f:
            f.write(f"{name},{date_str},{time_str},{Config.LOCATION}\n")
        
        # Mark as present
        self.marked_today.add(name)
        
        # Notifications
        self.esp32.send_command(f"SUCCESS:{name}")
        self.voice.speak(f"Welcome {name}, attendance marked")
        self.telegram.send_photo(name, photo_filename)
        self.dashboard.add_attendance(name, time_str)
        
        print(f"✅ Attendance marked for {name}")
        print(f"📸 Photo saved: {photo_filename}")
        
        return True
    
    def send_unknown(self):
        self.esp32.send_command("UNKNOWN")
        self.voice.speak("Unknown face detected, access denied")
    
    def reset(self):
        self.marked_today.clear()
        self.esp32.send_command("RESET")
        print("🔄 Attendance counter reset!")

# ==================== FACE RECOGNITION ENGINE ====================
class FaceRecognizer:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.check_database()
    
    def check_database(self):
        if not os.path.exists(Config.FACES_DB):
            os.makedirs(Config.FACES_DB)
            print(f"⚠️ Created folder: {Config.FACES_DB}")
        
        faces = [f for f in os.listdir(Config.FACES_DB) 
                if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        
        if len(faces) == 0:
            print("\n" + "="*60)
            print("⚠️ NO REGISTERED FACES FOUND!")
            print("="*60)
            print(f"📝 How to register faces:")
            print(f"   1. Add photos to '{Config.FACES_DB}' folder")
            print(f"   2. Name format: PersonName.jpg (e.g., John.jpg)")
            print(f"   3. Use clear, front-facing photos")
            print("="*60 + "\n")
            return False
        
        print(f"✅ Found {len(faces)} registered faces:")
        for face in faces:
            print(f"   • {os.path.splitext(face)[0]}")
        
        return True
    
    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        return faces
    
    def recognize_face(self, frame):
        try:
            temp_img = 'temp_recognition.jpg'
            cv2.imwrite(temp_img, frame)
            
            # Find matching face
            result = DeepFace.find(
                img_path=temp_img,
                db_path=Config.FACES_DB,
                model_name=Config.MODEL_NAME,
                distance_metric=Config.DISTANCE_METRIC,
                enforce_detection=True,
                silent=True
            )
            
            # Detect emotion
            try:
                emotion_result = DeepFace.analyze(
                    temp_img, 
                    actions=['emotion'], 
                    enforce_detection=False, 
                    silent=True
                )
                emotion = emotion_result[0]['dominant_emotion'] if isinstance(emotion_result, list) else emotion_result['dominant_emotion']
            except:
                emotion = "neutral"
            
            # Cleanup
            if os.path.exists(temp_img):
                os.remove(temp_img)
            
            # Process result
            if len(result) > 0 and len(result[0]) > 0:
                best_match = result[0].iloc[0]
                identity = best_match['identity']
                distance = best_match['distance']
                
                name = os.path.splitext(os.path.basename(identity))[0]
                
                # Calculate confidence
                if Config.DISTANCE_METRIC == 'cosine':
                    confidence = (1 - distance) * 100
                else:
                    confidence = max(0, 100 - (distance * 10))
                
                if confidence > Config.CONFIDENCE_THRESHOLD:
                    return name, confidence, emotion
            
            return None, 0, emotion
            
        except Exception as e:
            return None, 0, "neutral"

# ==================== MAIN APPLICATION ====================
class SmartAttendAI:
    def __init__(self):
        print("\n" + "╔" + "="*58 + "╗")
        print("║" + " "*15 + "SmartAttend AI System" + " "*22 + "║")
        print("╚" + "="*58 + "╝\n")
        
        # Initialize components
        print("🔧 Initializing components...")
        self.esp32 = ESP32Controller()
        self.voice = VoiceAnnouncer()
        self.telegram = TelegramNotifier()
        self.dashboard = WebDashboard()
        self.recognizer = FaceRecognizer()
        self.attendance = AttendanceManager(
            self.esp32, self.voice, self.telegram, self.dashboard
        )
        
        # Start web dashboard
        self.dashboard.start()
        
        # Recognition state
        self.current_name = "Unknown"
        self.current_confidence = 0
        self.current_emotion = "neutral"
        self.last_recognition_time = 0
    
    def draw_interface(self, frame, faces):
        # Periodic recognition
        current_time = time.time()
        if (current_time - self.last_recognition_time > Config.RECOGNITION_COOLDOWN 
            and len(faces) > 0):
            name, confidence, emotion = self.recognizer.recognize_face(frame)
            if name:
                self.current_name = name
                self.current_confidence = confidence
                self.current_emotion = emotion
            else:
                self.current_name = "Unknown"
                self.current_confidence = 0
            self.last_recognition_time = current_time
        
        # Draw face rectangles
        for (x, y, w, h) in faces:
            color = (0, 255, 0) if self.current_name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            
            # Labels
            if self.current_name != "Unknown":
                label = f"{self.current_name} ({self.current_confidence:.1f}%)"
            else:
                label = "Unknown"
            
            emotion_label = f"Emotion: {self.current_emotion}"
            
            # Background rectangle for text
            cv2.rectangle(frame, (x, y-60), (x+w, y), color, cv2.FILLED)
            cv2.putText(frame, label, (x+6, y-35), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, emotion_label, (x+6, y-10), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.4, (255, 255, 255), 1)
        
        # Status bar
        cv2.putText(frame, f"Present Today: {len(self.attendance.marked_today)}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Location: {Config.LOCATION}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Controls
        controls = "Press 'S' to scan | 'R' to reset | 'Q' to quit"
        cv2.putText(frame, controls, (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def run(self):
        if not self.recognizer.check_database():
            return
        
        # Initialize camera
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            print("❌ Failed to open camera!")
            return
        
        print("\n" + "="*60)
        print("📹 SmartAttend AI System Started!")
        print("="*60)
        print("🎮 Controls:")
        print("   'S' - Scan face and mark attendance")
        print("   'R' - Reset today's attendance counter")
        print("   'Q' - Quit application")
        print("="*60 + "\n")
        
        self.voice.speak("SmartAttend AI system ready")
        
        while True:
            ret, frame = video_capture.read()
            if not ret:
                print("❌ Failed to grab frame")
                break
            
            # Detect faces
            faces = self.recognizer.detect_faces(frame)
            
            # Draw interface
            frame = self.draw_interface(frame, faces)
            
            # Display
            cv2.imshow('SmartAttend AI - Face Recognition', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('s') or key == ord('S'):
                print("\n🔍 Scanning face...")
                
                if len(faces) == 0:
                    print("⚠️ No face detected!")
                    continue
                
                name, confidence, emotion = self.recognizer.recognize_face(frame)
                
                if name and confidence > Config.CONFIDENCE_THRESHOLD:
                    print(f"✅ Recognized: {name} ({confidence:.1f}%)")
                    print(f"😊 Emotion: {emotion}")
                    self.attendance.mark_attendance(name, frame)
                else:
                    print("❌ Unknown face detected!")
                    self.attendance.send_unknown()
            
            elif key == ord('r') or key == ord('R'):
                self.attendance.reset()
            
            elif key == ord('q') or key == ord('Q'):
                break
        
        # Cleanup
        video_capture.release()
        cv2.destroyAllWindows()
        self.esp32.close()
        print("\n👋 SmartAttend AI system closed!")
        self.voice.speak("System shutting down")

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    try:
        app = SmartAttendAI()
        app.run()
    except KeyboardInterrupt:
        print("\n\n⚠️ System interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()