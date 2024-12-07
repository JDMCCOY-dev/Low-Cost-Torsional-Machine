#include <Wire.h>
#include <CytronMotorDriver.h>
#include "SparkFun_Qwiic_Scale_NAU7802_Arduino_Library.h" //assuming the NAU7802 is being used as the qwiic scale

// Define motor and rotary encoder pins.. Pretty sure these are the correct pin numbers but maybe paired incorrectly
//#define MOTOR_A 4
//#define MOTOR_B 5
#define ENC_A 1
#define ENC_B 2
#define AVG_SIZE 10

CytronMD motor(PWM_DIR, 3, 4);
NAU7802 myScale; //Create instance of the NAU7802 class

unsigned long _lastIncReadTime = micros(); 
unsigned long _lastDecReadTime = micros(); 
int _pauseLength = 25000;
int _fastIncrement = 10;

volatile int counter = 0;

void setup() {
  // put your setup code here, to run once:

  // Global initializers
  _lastIncReadTime = micros();
  if (!myScale.begin()) {
    Serial.println("Scale initialization failed.");
    while (1);
  }

  //Set motor pins
  //pinMode(MOTOR_A, OUTPUT);
  //pinMode(MOTOR_B, OUTPUT);

  // Set encoder pins and attach interrupts
  pinMode(ENC_A, INPUT_PULLUP);
  pinMode(ENC_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_A), read_encoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_B), read_encoder, CHANGE);

  // Start the serial monitor to show output
  Serial.begin(115200); // value is 115,200 bits per second. faster communication
}

void loop() {
  // put your main code here, to run repeatedly:

  //Coding for Reading the Torque Cell
  int32_t currentReading = myScale.getReading();
  float currentWeight = myScale.getWeight();

  Serial.print("Reading: ");
  Serial.print(currentReading);
  Serial.print("\tWeight: ");
  Serial.print(currentWeight, 2); //Print 2 decimal places

  int avgWeightSpot = 0;
  float avgWeights[AVG_SIZE];
  avgWeights[avgWeightSpot++] = currentWeight;
  if (avgWeightSpot == AVG_SIZE) avgWeightSpot = 0;

  float avgWeight = 0;
  for (int x = 0; x < AVG_SIZE; x++)
    avgWeight += avgWeights[x];
  avgWeight /= AVG_SIZE;

  Serial.print("\tAvgWeight: ");
  Serial.print(avgWeight, 2); //Print 2 decimal places

  // Coding for Motor Control and Rotary Encoder
  int angle = 0;
  while (angle < 360) {
    static int lastCounter = 0;
    motor.setSpeed(0);

    // If count has changed print the new value to serial
    if (counter != lastCounter) {
      angle = counter * 0.18;
      Serial.println(angle);
      Serial.println(counter);
      Serial.println(micros());
      lastCounter - counter;
    }
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
