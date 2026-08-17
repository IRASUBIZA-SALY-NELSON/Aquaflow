/*
 * AquaFlow ESP32 Firmware (WiFi demo)
 * -----------------------------------
 * Wiring (as built):
 *   Primary flow sensor (SOURCE A)   -> GPIO 2   (D2)  [direct]
 *   Secondary flow sensor (TAP B)    -> GPIO 4   (D4)  [direct]
 *   Solenoid valve                   -> GPIO 27  [via RELAY]
 *   Water pump                       -> GPIO 14  [via RELAY]
 *   Buzzer                           -> GPIO 13  [via RELAY]
 *   Push button (manual override)    -> GPIO 12  (INPUT_PULLUP, active LOW)
 *
 * Relay modules: ACTIVE LOW (GPIO LOW = relay ON / coil energized)
 * Solenoid valve: NORMALLY CLOSED (NC)
 *   - Energized (relay ON)  => valve OPENS  => water can flow
 *   - De-energized (relay OFF) => valve CLOSES => water blocked (safe default / leak shutoff)
 *
 * Idle with sensors unplugged: buzzer OFF, pump OFF (no false leak from floating pins).
 *
 * Logic:
 *   A LOW, B LOW              -> IDLE
 *   A HIGH, B HIGH            -> NORMAL_USE / CONTINUOUS_FLOW
 *   A HIGH, B LOW (sustained) -> MID_PIPE_LEAK => solenoid CLOSED + pump OFF + buzzer
 *
 * Button:
 *   Single click  -> toggle solenoid (open/close water path)
 *   Double click  -> toggle pump/motor on or off
 *
 * POST JSON every 1s -> http://SERVER_HOST:9090/api/ingest
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ============ NETWORK ============
const char* WIFI_SSID     = "MTN UrugoNet_CBC4";
const char* WIFI_PASSWORD = "9255E65C";
const char* SERVER_HOST   = "192.168.0.115";
const uint16_t SERVER_PORT = 9090;
const char* DEVICE_ID     = "aquaflow-esp32-01";
// =================================

// Pins from your hardware
const int PIN_SENSOR_A = 2;    // primary / source
const int PIN_SENSOR_B = 4;    // secondary / tap
const int PIN_SOLENOID = 27;   // relay -> NC solenoid
const int PIN_PUMP     = 14;   // relay -> pump
const int PIN_BUZZER   = 13;   // relay -> buzzer
const int PIN_BUTTON   = 12;

// Your board: ACTIVE HIGH (HIGH=ON, LOW=OFF). Confirmed: active-low left buzzer ON when "off".
const bool RELAY_ACTIVE_LOW = false;

const float FLOW_ON_LPM        = 0.25f;  // ignore tiny noise
const uint32_t MIN_PULSES      = 5;      // <5 pulses/sec treated as 0 (disconnected/noise)
const uint32_t LEAK_CONFIRM_MS = 5000;
const uint32_t CONTINUOUS_MS   = 45000;
const uint32_t SAMPLE_MS       = 1000;
const uint32_t DEBOUNCE_MS     = 40;
const uint32_t DOUBLE_CLICK_MS = 450;
const uint32_t BOOT_GRACE_MS   = 12000;  // no alarms until sensors settle


volatile uint32_t pulsesA = 0;
volatile uint32_t pulsesB = 0;
float totalLitersA = 0.0f;
float totalLitersB = 0.0f;
bool solenoidOpen = true;  // semantic: water path open (NC valve energized)
bool pumpOn = false;
bool buzzerOn = false;
bool solenoidManualOverride = false;
bool pumpManualOverride = false;

uint32_t midLeakStart = 0;
uint32_t continuousStart = 0;
uint32_t lastSample = 0;
uint32_t lastBtnChange = 0;
uint32_t lastClickTime = 0;
uint8_t clickCount = 0;
bool lastBtnStable = HIGH;

void IRAM_ATTR onPulseA() { pulsesA++; }
void IRAM_ATTR onPulseB() { pulsesB++; }

// Drive a relay channel: on=true means device powered / relay coil ON
void relayWrite(int pin, bool on) {
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(pin, on ? LOW : HIGH);
  } else {
    digitalWrite(pin, on ? HIGH : LOW);
  }
}

void setBuzzer(bool on) {
  buzzerOn = on;
  relayWrite(PIN_BUZZER, on);
}

void setPump(bool on) {
  pumpOn = on;
  relayWrite(PIN_PUMP, on);
}

void setSolenoid(bool openValve) {
  // NC solenoid: openValve=true => energize coil (relay ON) => valve opens
  //              openValve=false => de-energize (relay OFF) => valve closes
  solenoidOpen = openValve;
  relayWrite(PIN_SOLENOID, openValve);
  if (!openValve) {
    setPump(false);
  }
}

void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) return;

  WiFi.mode(WIFI_STA);
  WiFi.disconnect(false, true);
  delay(100);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("WiFi connecting to ");
  Serial.println(WIFI_SSID);

  // Non-blocking-ish: wait at most 8s so sensors keep updating
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 8000) {
    delay(250);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi OK: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.print("WiFi not ready, status=");
    Serial.println((int)WiFi.status());
  }
}

String classify(float aLpm, float bLpm, bool& leakMid, bool& continuous) {
  bool aOn = aLpm >= FLOW_ON_LPM;
  bool bOn = bLpm >= FLOW_ON_LPM;
  leakMid = false;
  continuous = false;

  if (!aOn && !bOn) {
    midLeakStart = 0;
    continuousStart = 0;
    return "IDLE";
  }

  if (aOn && bOn) {
    midLeakStart = 0;
    if (continuousStart == 0) continuousStart = millis();
    if (millis() - continuousStart >= CONTINUOUS_MS) {
      continuous = true;
      return "CONTINUOUS_FLOW";
    }
    return "NORMAL_USE";
  }

  if (aOn && !bOn) {
    continuousStart = 0;
    if (midLeakStart == 0) midLeakStart = millis();
    if (millis() - midLeakStart >= LEAK_CONFIRM_MS) {
      leakMid = true;
      return "MID_PIPE_LEAK";
    }
    return "SUSPECT_LEAK";
  }

  midLeakStart = 0;
  return "SENSOR_MISMATCH";
}

void handleButton() {
  bool raw = digitalRead(PIN_BUTTON);
  if (raw != lastBtnStable && (millis() - lastBtnChange) > DEBOUNCE_MS) {
    lastBtnChange = millis();
    lastBtnStable = raw;
    if (raw == LOW) {  // pressed (active LOW)
      uint32_t now = millis();
      if (now - lastClickTime <= DOUBLE_CLICK_MS) {
        clickCount++;
      } else {
        clickCount = 1;
      }
      lastClickTime = now;
    }
  }

  // Resolve click gesture after quiet window
  if (clickCount > 0 && (millis() - lastClickTime) > DOUBLE_CLICK_MS) {
    if (clickCount == 1) {
      // Single click: toggle solenoid only
      solenoidManualOverride = true;
      setSolenoid(!solenoidOpen);
      Serial.println(solenoidOpen ? "{\"event\":\"button_solenoid_open\"}" : "{\"event\":\"button_solenoid_close\"}");
    } else {
      // Double click: toggle pump/motor only
      pumpManualOverride = true;
      setPump(!pumpOn);
      Serial.println(pumpOn ? "{\"event\":\"button_pump_on\"}" : "{\"event\":\"button_pump_off\"}");
    }
    clickCount = 0;
  }
}

void postIngest(const String& payload) {
  static uint32_t lastAttempt = 0;
  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - lastAttempt < 10000) return;  // don't spam reconnect
    lastAttempt = millis();
    connectWifi();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  HTTPClient http;
  String url = String("http://") + SERVER_HOST + ":" + SERVER_PORT + "/api/ingest";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Id", DEVICE_ID);
  int code = http.POST(payload);
  if (code > 0) {
    String resp = http.getString();
    StaticJsonDocument<256> doc;
    if (!deserializeJson(doc, resp)) {
      if (!solenoidManualOverride && doc.containsKey("solenoid_open")) {
        bool wantOpen = doc["solenoid_open"].as<bool>();
        setSolenoid(wantOpen);
      }
    }
  } else {
    Serial.printf("HTTP post failed: %s\n", http.errorToString(code).c_str());
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  delay(200);

  pinMode(PIN_SENSOR_A, INPUT_PULLUP);
  pinMode(PIN_SENSOR_B, INPUT_PULLUP);
  pinMode(PIN_SOLENOID, OUTPUT);
  pinMode(PIN_PUMP, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);

  // Safe OFF first (ACTIVE HIGH relays => LOW = OFF)
  digitalWrite(PIN_SOLENOID, LOW);
  digitalWrite(PIN_PUMP, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  delay(50);

  // Quiet boot: buzzer OFF, pump OFF. Open NC solenoid for demo water path.
  setBuzzer(false);
  setPump(false);
  setSolenoid(true);

  delay(300);
  noInterrupts();
  pulsesA = 0;
  pulsesB = 0;
  interrupts();
  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_A), onPulseA, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_B), onPulseB, FALLING);

  connectWifi();
  lastSample = millis();
  Serial.println("{\"boot\":\"AquaFlow ESP32 ready\",\"relay\":\"active_high\",\"solenoid\":\"NC\",\"pins\":\"A2 B4 SOL27 PUMP14 BUZ13 BTN12\"}");
}

void loop() {
  handleButton();

  if (millis() - lastSample < SAMPLE_MS) return;
  lastSample = millis();

  noInterrupts();
  uint32_t countA = pulsesA;
  uint32_t countB = pulsesB;
  pulsesA = 0;
  pulsesB = 0;
  interrupts();

  // Noise gate: unconnected / EMI on GPIO2/4 can fake pulses
  if (countA < MIN_PULSES) countA = 0;
  if (countB < MIN_PULSES) countB = 0;

  float aLpm = countA / 7.5f;
  float bLpm = countB / 7.5f;
  float aLps = aLpm / 60.0f;
  float bLps = bLpm / 60.0f;
  totalLitersA += aLps;
  totalLitersB += bLps;

  bool leakMid = false;
  bool continuous = false;
  String status = classify(aLpm, bLpm, leakMid, continuous);

  // During boot grace: force quiet (sensors may be disconnected)
  if (millis() < BOOT_GRACE_MS) {
    status = "IDLE";
    leakMid = false;
    continuous = false;
    midLeakStart = 0;
    continuousStart = 0;
    setBuzzer(false);
    setPump(false);
  } else if (leakMid) {
    solenoidManualOverride = false;
    pumpManualOverride = false;
    setSolenoid(false);
    setPump(false);
    setBuzzer(true);
  } else if (status == "SUSPECT_LEAK") {
    setBuzzer((millis() / 300) % 2 == 0);
  } else if (status == "CONTINUOUS_FLOW") {
    setBuzzer((millis() / 700) % 2 == 0);
  } else if (status == "NORMAL_USE") {
    setBuzzer(false);
    if (!solenoidManualOverride) {
      setSolenoid(true);
    }
    if (!pumpManualOverride) {
      setPump(true);
    }
  } else {  // IDLE / SENSOR_MISMATCH / anything else quiet
    setBuzzer(false);
    if (!pumpManualOverride) {
      setPump(false);
    }
  }

  StaticJsonDocument<640> doc;
  doc["device_id"] = DEVICE_ID;
  doc["ts"] = (uint32_t)(millis() / 1000);
  doc["flow_a_lpm"] = aLpm;
  doc["flow_b_lpm"] = bLpm;
  doc["flow_a_lps"] = aLps;
  doc["flow_b_lps"] = bLps;
  doc["total_a_l"] = totalLitersA;
  doc["total_b_l"] = totalLitersB;
  doc["status"] = status;
  doc["leak_mid"] = leakMid;
  doc["continuous_flow"] = continuous;
  doc["solenoid_open"] = solenoidOpen;
  doc["pump_on"] = pumpOn;
  doc["buzzer_on"] = buzzerOn;
  doc["manual_override"] = solenoidManualOverride;
  doc["pump_manual_override"] = pumpManualOverride;
  doc["wifi_rssi"] = WiFi.RSSI();

  String payload;
  serializeJson(doc, payload);
  Serial.println(payload);
  postIngest(payload);
}
