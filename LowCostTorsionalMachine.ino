#include <CytronMotorDriver.h>
#include <Wire.h>
#include <SparkFun_Qwiic_Scale_NAU7802_Arduino_Library.h>

//Configure motor driver. 
CytronMD motor(PWM_DIR, 5, 4);

// Qwiic Scale Setup
NAU7802 qwiicScale;

// Define rotary encoder pins
#define ENC_A 3
#define ENC_B 2

// Used in Encoder function
volatile int counter = 0;
unsigned long _lastIncReadTime = micros(); 
unsigned long _lastDecReadTime = micros(); 
int _pauseLength = 25000;
int _fastIncrement = 10;

// Control Variables for Serial functionality
float position = 0.0;
float targetAngle = 0.0;
float speedDegPerMin = 0.0;
bool testRunning = false;
bool directionClockwise = true;
unsigned long lastDataSendTime = 0;
const unsigned long dataInterval = 200; // unit is ms.. controls rate of angle/torque data output
float calibrationFactor = 1.0; // Raw reading to torque scale (Nm)

void setup() {
  // Start the serial monitor to show output
  Serial.begin(9600);

  // Set encoder pins and attach interrupts
  pinMode(ENC_A, INPUT_PULLUP);
  pinMode(ENC_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_A), read_encoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_B), read_encoder, CHANGE);

  // Qwiic Scale Setup
    Wire.begin();
    // short hand for if qwiicscale is not true or == false
    if (!qwiicScale.begin()) {
        Serial.println("Qwiic Scale not detected!");
    } else {
        qwiicScale.calculateZeroOffset();
        qwiicScale.setGain(NAU7802_GAIN_128);
        Serial.println("Qwiic Scale ready");
    }

    // Final Status confirmation
    Serial.println("System Ready");
}

void loop() {
  handleSerial();

  position = counter * 0.018347168;  // Convert encoder count to degrees
  // float torque = qwiicScale.getReading() * calibrationFactor; // Read torque
  float torque = 0.0;
  unsigned long start = millis();
  while (!qwiicScale.available() && (millis() - start < 500)) {
    // Wait up to 500 ms for reading
  }
  if (qwiicScale.available()) {
    torque = qwiicScale.getReading() * calibrationFactor;
  } else {
    Serial.println("Torque read timeout");
  }

  if (testRunning) {
    // Check torque limit first
    if (torque >= 145.0) {
      motor.setSpeed(0);
      testRunning = false;
      Serial.println("Torque limit exceeded! Test Aborted.");
    }
    // Check if target angle reached
    else if ((directionClockwise && position >= targetAngle) ||
        (!directionClockwise && position <= -targetAngle)) {
      motor.setSpeed(0);
      testRunning = false;
      Serial.println("Reached target angle. Test complete.");
    }
    else {
      int speedPWM = (directionClockwise ? 1 : -1) * 2 * constrain(map(speedDegPerMin, 0, 180, 90, 255), 90, 255);
      motor.setSpeed(speedPWM);
    }

    // Periodic data print
    if (millis() - lastDataSendTime >= dataInterval) {
      Serial.print("ANGLE:");
      Serial.print(position, 2);
      Serial.print(",TORQUE:");
      Serial.println(qwiicScale.getReading() * calibrationFactor, 5); // convert to N*m
      lastDataSendTime = millis();
    }
  }
}

void handleSerial() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd.startsWith("SET ANGLE")) {
      targetAngle = cmd.substring(10).toFloat();
      Serial.print("Target Angle Set to: ");
      Serial.println(targetAngle);
    } 
    else if (cmd.startsWith("SET SPEED")) {
      speedDegPerMin = cmd.substring(10).toFloat();
      Serial.print("Target Speed Set to: ");
      Serial.print(speedDegPerMin);
      Serial.println(" deg/min");
    } 
    else if (cmd.startsWith("DIRECTION")) {
      if (cmd.endsWith("CCW")) {
        directionClockwise = false;
      }
      else if (cmd.endsWith("CW")) {
        directionClockwise = true;
      }
      Serial.print("Direction Set: ");
      Serial.println(directionClockwise ? "Clockwise" : "Counter-Clockwise");
    }
    else if (cmd == "START") {
      counter = 0; // Reset encoder for new test
      position = 0;
      testRunning = true;
      Serial.println("Test started");
    } 
    else if (cmd == "STOP") {
      testRunning = false;
      motor.setSpeed(0);
      Serial.println("Test stopped");
    } 
    else if (cmd == "TARE") {
      Serial.println("Smart Taring and Calibrating scale... please wait.");

      long avgReading = 0;
      int sampleCount = 64;
      int validSamples = 0;

      for (int i = 0; i < sampleCount; i++) {
        while (qwiicScale.available() == false) {
          // Wait until a new reading is ready
        }
        long reading = qwiicScale.getReading();
        avgReading += reading;
        validSamples++;
        delay(5);
      }

      if (validSamples > 0) {
        avgReading /= validSamples;
        qwiicScale.setZeroOffset(avgReading);

        Serial.print("Smart tare complete. New zero offset = ");
        Serial.println(avgReading);

        // --- NEW Calibration auto-setup ---
        delay(100); // short wait

        if (qwiicScale.available()) {
          long postTareReading = qwiicScale.getReading(); // Read raw sensor output after tare
          float knownTorque = 0.01; // Nm, your "expected" reading
          if (postTareReading != 0) {
            calibrationFactor = knownTorque / postTareReading; // Compute calibration
            Serial.print("Auto-calibration complete. Calibration factor = ");
            Serial.println(calibrationFactor, 8);
          } else {
            Serial.println("Post-tare reading was zero, skipping calibration.");
          }
        } else {
          Serial.println("No valid reading after tare for calibration.");
        }
        // --- End NEW ---
      } else {
        Serial.println("Smart tare failed. No valid readings.");
      }
    }
    else if (cmd.startsWith("SET CALIBRATION")) {
      calibrationFactor = cmd.substring(16).toFloat();
      Serial.print("Calibration factor set to: ");
      Serial.println(calibrationFactor, 8);
    }
  }
}

// Pulled from folder sent from Dr. Elder.. encoder interrupt handler
void read_encoder() {
  // Encoder interrupt routine for both pins. Updates counter
  // if they are valid and have rotated a full indent
 
  static uint8_t old_AB = 3;  // Lookup table index
  static int8_t encval = 0;   // Encoder value  
  static const int8_t enc_states[]  = {0,-1,1,0,1,0,0,-1,-1,0,0,1,0,1,-1,0}; // Lookup table

  old_AB <<=2;  // Remember previous state

  if (digitalRead(ENC_A)) old_AB |= 0x02; // Add current state of pin A
  if (digitalRead(ENC_B)) old_AB |= 0x01; // Add current state of pin B
  
  encval += enc_states[( old_AB & 0x0f )];

  // Update counter if encoder has rotated a full indent, that is at least 4 steps
  if( encval > 3 ) {        // Four steps forward
    int changevalue = 1;
    if((micros() - _lastIncReadTime) < _pauseLength) {
      changevalue = _fastIncrement * changevalue; 
    }
    _lastIncReadTime = micros();
    counter = counter + changevalue;              // Update counter
    encval = 0;
  }
  else if( encval < -3 ) {        // Four steps backward
    int changevalue = -1;
    if((micros() - _lastDecReadTime) < _pauseLength) {
      changevalue = _fastIncrement * changevalue; 
    }
    _lastDecReadTime = micros();
    counter = counter + changevalue;              // Update counter
    encval = 0;
  }
} 
