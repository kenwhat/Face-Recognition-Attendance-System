# Face Recognition Attendance System

An AI-powered attendance tracking system using facial recognition with ESP32 hardware integration. The system captures and recognizes faces in real-time, logs attendance records, and provides hardware feedback through LCD displays, RGB LEDs, and buzzers.

## Features

✨ **Core Features**
- Real-time face recognition using DeepFace (Facenet model)
- Automatic attendance logging to CSV
- ESP32 hardware integration for physical feedback
- LCD display for user information
- RGB LED status indicators
- Buzzer notifications
- Voice announcements (optional)
- Telegram bot notifications (optional)

🔒 **Security**
- Cosine distance-based face matching
- Configurable confidence thresholds
- Cooldown period to prevent duplicate recognition
- Environment-based credentials management

## Project Structure

```
Face_Recognition_Project/
├── test_face_recognition.py          # Main Python application
├── facial_recognition_attendance_system_copy_2_copy_20251127042906.ino  # Arduino/ESP32 firmware
├── attendance.csv                     # Attendance records (auto-generated)
├── registered_faces/                  # Database of registered face encodings
├── captured_faces/                    # Temporary captured face images
├── .env                              # Environment variables (not committed)
├── .env.example                      # Example environment configuration
├── .gitignore                        # Git ignore rules
└── README.md                         # This file
```

## Requirements

### Hardware
- **ESP32 Development Board**
- **16x2 LCD Display** (I2C interface, address 0x27 or 0x3F)
- **RGB LED** (Common Anode)
- **Buzzer** (5V compatible)
- **USB Cable** for programming ESP32

### Software
- Python 3.8+
- pip (Python package manager)

## Installation

### 1. Clone or Download Repository
```bash
git clone <repository-url>
cd Face_Recognition_Project
```

### 2. Create Virtual Environment
```bash
python -m venv myenv
myenv\Scripts\activate  # Windows
source myenv/bin/activate  # Linux/Mac
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Copy the example file
copy .env.example .env

# Edit .env and add your actual configuration
# - ESP32 COM port
# - Telegram credentials (optional)
# - Other settings
```

### 5. Upload Arduino Firmware to ESP32
1. Open `facial_recognition_attendance_system_copy_2_copy_20251127042906.ino` in Arduino IDE
2. Select **Tools > Board > ESP32 Dev Module**
3. Select the correct COM port
4. Click **Upload**

## Configuration

Edit `.env` file with your settings:

```env
# ESP32 Serial Port
ESP32_PORT=COM5              # Windows: COM3-COM9, Linux: /dev/ttyUSB0, Mac: /dev/cu.usbserial

# Telegram Notifications
TELEGRAM_ENABLED=False
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Location Display
LOCATION=Main Building - Gate A

# Voice Announcements
VOICE_ENABLED=True
VOICE_RATE=150

# Face Recognition Model
MODEL_NAME=Facenet
DISTANCE_METRIC=cosine
CONFIDENCE_THRESHOLD=60      # 0-100, higher = stricter matching
RECOGNITION_COOLDOWN=2       # Seconds between recognitions
```

## Usage

### Start the System
```bash
python test_face_recognition.py
```

### Register a New Face
1. Run the system
2. Follow on-screen prompts to capture face from camera
3. Save person's name and face encoding
4. Face is stored in `registered_faces/` directory

### Mark Attendance
1. System continuously monitors camera
2. When a registered face is detected:
   - ✅ Green LED indicates recognition
   - 🔔 Buzzer beeps (2 tones)
   - 📱 Attendance logged to `attendance.csv`
   - 🔊 Voice announcement (if enabled)
   - 📤 Telegram notification (if enabled)

### View Attendance Records
Attendance is saved in `attendance.csv` with:
- Person name
- Recognition confidence (%)
- Date and time
- Location

## Hardware Pin Configuration (ESP32)

| Component | Pin |
|-----------|-----|
| LCD SDA | GPIO 21 |
| LCD SCL | GPIO 22 |
| RGB LED Red | GPIO 25 |
| RGB LED Green | GPIO 26 |
| RGB LED Blue | GPIO 27 |
| Buzzer | GPIO 14 |

## Security Notes

⚠️ **Important**
- Never commit credentials to Git (use `.env`)
- Keep `registered_faces/` private (added to `.gitignore`)
- Telegram tokens and WiFi passwords are stored locally only
- Face data contains biometric information — handle responsibly
- Use `.env.example` as template for other users

## Troubleshooting

### ESP32 Connection Failed
- Check COM port in `.env` (Windows Device Manager to find correct port)
- Verify USB cable connection
- Install CH340 drivers if needed

### Face Recognition Not Working
- Ensure good lighting
- Increase `CONFIDENCE_THRESHOLD` if getting false positives
- Check face is in `registered_faces/` directory

### No Sound Output
- Enable `VOICE_ENABLED=True` in `.env`
- Check system volume
- Verify speakers/headphones connected

## Requirements File

See `requirements.txt` for all Python dependencies:
- opencv-python (CV2)
- deepface
- tensorflow
- flask
- pyserial
- pyttsx3
- requests

## License

[Add your license here]

## Support

For issues or questions, please create an issue or contact the project maintainer.

---

**Last Updated:** February 2025
