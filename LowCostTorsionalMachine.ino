#include <CytronMotorDriver.h>
#include <Wire.h>
#include <SparkFun_Qwiic_Scale_NAU7802.h>

//Configure motor driver. 
CytronMD motor(PWM_DIR, 5, 4);

// Qwiic Scale Setup
NAU7802 qwiicScale;

// Define rotary encoder pins
#define ENC_A 3
#define ENC_B 2

// Used in Encoder function
unsigned long _lastIncReadTime = micros(); 
unsigned long _lastDecReadTime = micros(); 
int _pauseLength = 25000;
int _fastIncrement = 10;


volatile int counter = 0;

void setup() {
  // Start the serial monitor to show output
  Serial.begin(115200);

  // Set encoder pins and attach interrupts
  pinMode(ENC_A, INPUT_PULLUP);
  pinMode(ENC_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_A), read_encoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_B), read_encoder, CHANGE);

  // Qwiic Scale Setup
    Wire.begin();
    if (qwiicScale.begin() == false) {
        Serial.println("Qwiic Scale not detected!");
    } else {
        qwiicScale.calculateZeroOffset();
        qwiicScale.setGain(NAU7802_GAIN_128);
    }
}

void loop() {
  static int lastCounter = 0;

  // If count has changed, update motor speed and print value
  if(counter != lastCounter){
    float position = counter * 0.018347168;  // Convert encoder count to position
    int speed = map(counter, -100, 100, -255, 255);  // Map encoder count to motor speed range (-255 to 255)

    motor.setSpeed(speed);  // Set motor speed

    Serial.print("Position: ");
    Serial.println(position);
    Serial.print("Motor Speed: ");
    Serial.println(speed);
    
    lastCounter = counter;
  }
}


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
