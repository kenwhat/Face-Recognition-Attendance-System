#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>

// ==================== WIFI CONFIGURATION ====================
const char* ssid = "NotTheWi-FiYou'reLookingFor";
const char* password = "Omandam101!!!";

// ==================== HARDWARE PINS ====================
// LCD I2C (Default ESP32 I2C pins)
#define SDA_PIN 21
#define SCL_PIN 22

// RGB LED pins (Common Anode)
const int redPin = 25;
const int greenPin = 26;
const int bluePin = 27;

// Buzzer
const int buzzerPin = 14;

// ==================== COMPONENT INITIALIZATION ====================
LiquidCrystal_I2C lcd(0x27, 16, 2);  // Try 0x3F if 0x27 doesn't work

// ==================== GLOBAL VARIABLES ====================
int totalPresent = 0;

// ==================== RGB LED FUNCTIONS ====================
// For Common Anode RGB LED (inverted logic)
void setColor(int red, int green, int blue) {
  analogWrite(redPin, 255 - red);
  analogWrite(greenPin, 255 - green);
  analogWrite(bluePin, 255 - blue);
}

void ledOff() { setColor(0, 0, 0); }
void ledGreen() { setColor(0, 255, 0); }
void ledRed() { setColor(255, 0, 0); }
void ledOrange() { setColor(255, 165, 0); }
void ledBlue() { setColor(0, 0, 255); }
void ledPurple() { setColor(128, 0, 128); }

// ==================== LOUD BUZZER FUNCTIONS ====================
void beepSuccess() {
  // Double beep - loud and clear
  tone(buzzerPin, 2000, 300);
  delay(350);
  tone(buzzerPin, 2500, 300);
}

void beepError() {
  // Triple harsh beep - very loud
  for (int i = 0; i < 3; i++) {
    tone(buzzerPin, 400, 250);
    delay(300);
  }
}

void beepWarning() {
  // Long warning beep
  tone(buzzerPin, 1000, 500);
  delay(100);
  tone(buzzerPin, 1000, 500);
}

void beepReset() {
  // Ascending tone - loud reset sound
  tone(buzzerPin, 1500, 200);
  delay(250);
  tone(buzzerPin, 2000, 200);
  delay(250);
  tone(buzzerPin, 2500, 200);
}

void beepStartup() {
  // System startup melody - loud
  tone(buzzerPin, 1000, 150);
  delay(200);
  tone(buzzerPin, 1500, 150);
  delay(200);
  tone(buzzerPin, 2000, 300);
}

// ==================== LCD DISPLAY FUNCTIONS ====================
void updateDisplay(String line1, String line2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
}

void displayCentered(String text, int row) {
  int padding = (16 - text.length()) / 2;
  lcd.setCursor(padding > 0 ? padding : 0, row);
  lcd.print(text);
}

// ==================== WIFI SETUP ====================
bool setupWiFi() {
  ledBlue();
  updateDisplay("Connecting WiFi", "Please wait...");
  
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  Serial.println();
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("✅ WiFi Connected!");
    Serial.print("📶 Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    Serial.print("🌐 IP Address: ");
    Serial.println(WiFi.localIP());
    
    updateDisplay("WiFi Connected!", WiFi.localIP().toString());
    ledGreen();
    beepSuccess();
    delay(2000);
    return true;
  } else {
    Serial.println("⚠️ WiFi Connection Failed!");
    Serial.println("💡 System will work offline");
    updateDisplay("WiFi Failed!", "Offline Mode");
    ledOrange();
    beepWarning();
    delay(2000);
    return false;
  }
}

// ==================== EVENT HANDLERS ====================
void handleSuccess(String name) {
  totalPresent++;
  
  Serial.println("✅ SUCCESS: " + name);
  
  // Display welcome message
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Welcome!");
  lcd.setCursor(0, 1);
  lcd.print(name.length() > 16 ? name.substring(0, 16) : name);
  
  // Green LED with loud success beep
  ledGreen();
  beepSuccess();
  
  delay(2000);
  
  // Show total count
  updateDisplay("Marked Present", "Total: " + String(totalPresent));
  delay(2000);
  
  // Return to waiting screen
  ledOff();
  updateDisplay("Waiting...", "Present: " + String(totalPresent));
}

void handleUnknown() {
  Serial.println("❌ UNKNOWN FACE");
  
  updateDisplay("Access Denied!", "Unknown Face");
  
  // Red LED with loud error beeps
  ledRed();
  beepError();
  
  delay(2000);
  
  ledOff();
  updateDisplay("Waiting...", "Present: " + String(totalPresent));
}

void handleAlready(String name) {
  Serial.println("⚠️ ALREADY MARKED: " + name);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(name.length() > 16 ? name.substring(0, 16) : name);
  lcd.setCursor(0, 1);
  lcd.print("Already Marked!");
  
  // Orange LED with loud warning
  ledOrange();
  beepWarning();
  
  delay(2000);
  
  ledOff();
  updateDisplay("Waiting...", "Present: " + String(totalPresent));
}

void handleReset() {
  totalPresent = 0;
  
  Serial.println("🔄 COUNTER RESET");
  
  updateDisplay("Counter Reset!", "Present: 0");
  
  // Blue LED with loud reset beeps
  ledBlue();
  beepReset();
  
  delay(1500);
  
  ledOff();
  updateDisplay("Waiting...", "Present: 0");
}

// ==================== SERIAL COMMAND PROCESSOR ====================
void processCommand(String command) {
  command.trim();
  
  if (command.length() == 0) return;
  
  Serial.print("📥 Received: ");
  Serial.println(command);
  
  if (command.startsWith("SUCCESS:")) {
    String name = command.substring(8);
    handleSuccess(name);
    
  } else if (command == "UNKNOWN") {
    handleUnknown();
    
  } else if (command.startsWith("ALREADY:")) {
    String name = command.substring(8);
    handleAlready(name);
    
  } else if (command == "RESET") {
    handleReset();
    
  } else {
    Serial.println("⚠️ Unknown command: " + command);
  }
}

// ==================== SETUP ====================
void setup() {
  // Initialize Serial
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\n╔════════════════════════════════════╗");
  Serial.println("║   SmartAttend AI - ESP32 System   ║");
  Serial.println("╚════════════════════════════════════╝\n");
  
  // Initialize I2C
  Wire.begin(SDA_PIN, SCL_PIN);
  Serial.println("✅ I2C initialized");
  
  // Initialize LCD
  lcd.init();
  lcd.backlight();
  lcd.clear();
  Serial.println("✅ LCD initialized");
  
  // Setup RGB LED pins
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  ledOff();
  Serial.println("✅ RGB LED initialized");
  
  // Setup buzzer
  pinMode(buzzerPin, OUTPUT);
  Serial.println("✅ Buzzer initialized");
  
  // Connect to WiFi
  Serial.println("\n🌐 Connecting to WiFi...");
  setupWiFi();
  
  // Show ready message with loud startup sound
  ledOff();
  lcd.clear();
  displayCentered("SmartAttend AI", 0);
  displayCentered("System Ready!", 1);
  ledBlue();
  beepStartup();
  delay(2000);
  ledOff();
  
  // Show waiting screen
  updateDisplay("Waiting...", "Present: 0");
  
  Serial.println("\n✅ System Ready!");
  Serial.println("📋 Commands: SUCCESS:<name>, UNKNOWN, ALREADY:<name>, RESET");
  Serial.println("═══════════════════════════════════════════════════\n");
}

// ==================== MAIN LOOP ====================
void loop() {
  // Check for serial commands from Python
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    processCommand(command);
  }
  
  // Small delay to prevent excessive CPU usage
  delay(10);
}