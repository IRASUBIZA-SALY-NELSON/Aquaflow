// ================================
// Water Flow Sensor – Arduino Uno
// Signal pin: D2
// Power: 5V, GND
// ================================

// Pulse counter (must be volatile)
volatile unsigned long pulseCount = 0;

// Flow variables
float flowRateLpm = 0.0;      // Liters per minute
float flowRateLps = 0.0;      // Liters per second
float totalLiters = 0.0;      // Total water passed

unsigned long lastTime = 0;

// Interrupt service routine
void pulseCounter() {
  pulseCount++;
}

void setup() {
  Serial.begin(9600);

  pinMode(2, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(2), pulseCounter, FALLING);
  Serial.println("Water Flow Sensor Started...");
}

void loop() {
  if (millis() - lastTime >= 1000) {   // Every 1 second
    detachInterrupt(digitalPinToInterrupt(2));
    // Standard calibration for YF-S201
    flowRateLpm = pulseCount / 7.5;      // Liters per minute
    flowRateLps = flowRateLpm / 60.0;    // Liters per second

    // Accumulate total water
    totalLiters += flowRateLps;

    // Display values
    Serial.print("Flow: ");
    Serial.print(flowRateLpm, 2);
    Serial.print(" L/min | ");

    Serial.print(flowRateLps, 3);
    Serial.print(" L/sec | ");

    Serial.print("Total: ");
    Serial.print(totalLiters, 3);
    Serial.println(" L");

    // Reset pulse counter
    pulseCount = 0;
    lastTime = millis();

    // Reattach interrupt
    attachInterrupt(digitalPinToInterrupt(2), pulseCounter, FALLING);
  }
}
