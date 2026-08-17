/*
 * AquaFlow Arduino Uno — Dual Flow Sensors (USB Serial demo)
 * ----------------------------------------------------------
 * Use this if ESP32 WiFi is not connected yet.
 * Backend reads Serial JSON lines at 9600 baud.
 *
 * Wiring:
 *   Sensor A SOURCE  -> D2 (interrupt 0)
 *   Sensor B TAP/END -> D3 (interrupt 1)
 *   Solenoid relay   -> D7 (HIGH = OPEN)
 *   LED              -> D13
 *
 * Open mid-pipe hole to demo MID_PIPE_LEAK (A flow, B near zero).
 */

const int PIN_SENSOR_A = 2;
const int PIN_SENSOR_B = 3;
const int PIN_SOLENOID = 7;
const int PIN_LED = 13;

const float FLOW_ON_LPM = 0.15;
const unsigned long LEAK_CONFIRM_MS = 5000;
const unsigned long CONTINUOUS_MS = 45000;
const unsigned long SAMPLE_MS = 1000;

volatile unsigned long pulsesA = 0;
volatile unsigned long pulsesB = 0;

float totalA = 0.0;
float totalB = 0.0;
bool solenoidOpen = true;
unsigned long midLeakStart = 0;
unsigned long continuousStart = 0;
unsigned long lastSample = 0;

void pulseA() { pulsesA++; }
void pulseB() { pulsesB++; }

void setSolenoid(bool openValve) {
  solenoidOpen = openValve;
  digitalWrite(PIN_SOLENOID, openValve ? HIGH : LOW);
  digitalWrite(PIN_LED, openValve ? LOW : HIGH);
}

String classify(float aLpm, float bLpm, bool &leakMid, bool &continuous) {
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

void setup() {
  Serial.begin(9600);
  pinMode(PIN_SENSOR_A, INPUT_PULLUP);
  pinMode(PIN_SENSOR_B, INPUT_PULLUP);
  pinMode(PIN_SOLENOID, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  setSolenoid(true);

  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_A), pulseA, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_B), pulseB, FALLING);
  lastSample = millis();
  Serial.println("{\"boot\":\"AquaFlow Uno Dual Ready\"}");
}

void loop() {
  if (millis() - lastSample < SAMPLE_MS) return;
  lastSample = millis();

  noInterrupts();
  unsigned long countA = pulsesA;
  unsigned long countB = pulsesB;
  pulsesA = 0;
  pulsesB = 0;
  interrupts();

  float aLpm = countA / 7.5;
  float bLpm = countB / 7.5;
  float aLps = aLpm / 60.0;
  float bLps = bLpm / 60.0;
  totalA += aLps;
  totalB += bLps;

  bool leakMid = false;
  bool continuous = false;
  String status = classify(aLpm, bLpm, leakMid, continuous);

  if (leakMid) {
    setSolenoid(false);
  } else if (status == "NORMAL_USE" && !solenoidOpen) {
    setSolenoid(true);
  }

  // Compact JSON for Python backend parser
  Serial.print("{\"device_id\":\"uno-dual-01\"");
  Serial.print(",\"flow_a_lpm\":"); Serial.print(aLpm, 2);
  Serial.print(",\"flow_b_lpm\":"); Serial.print(bLpm, 2);
  Serial.print(",\"flow_a_lps\":"); Serial.print(aLps, 3);
  Serial.print(",\"flow_b_lps\":"); Serial.print(bLps, 3);
  Serial.print(",\"total_a_l\":"); Serial.print(totalA, 3);
  Serial.print(",\"total_b_l\":"); Serial.print(totalB, 3);
  Serial.print(",\"status\":\""); Serial.print(status); Serial.print("\"");
  Serial.print(",\"leak_mid\":"); Serial.print(leakMid ? "true" : "false");
  Serial.print(",\"continuous_flow\":"); Serial.print(continuous ? "true" : "false");
  Serial.print(",\"solenoid_open\":"); Serial.print(solenoidOpen ? "true" : "false");
  Serial.println("}");
}
