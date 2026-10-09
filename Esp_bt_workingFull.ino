#include "BluetoothSerial.h"

// ========================================
// RIDEGUARD - BLUETOOTH CLASSIC HAPTIC
// ========================================

BluetoothSerial SerialBT;

// LEFT MOTORS
const int LEFT_MOTOR_1 = 14;
const int LEFT_MOTOR_2 = 2;

// RIGHT MOTORS
const int RIGHT_MOTOR_1 = 4;
const int RIGHT_MOTOR_2 = 27;


// ========================================
// MOTOR CONTROL
// ========================================

void allOff() {

  digitalWrite(LEFT_MOTOR_1, LOW);
  digitalWrite(LEFT_MOTOR_2, LOW);

  digitalWrite(RIGHT_MOTOR_1, LOW);
  digitalWrite(RIGHT_MOTOR_2, LOW);
}


void leftMotorsOn() {

  digitalWrite(RIGHT_MOTOR_1, LOW);
  digitalWrite(RIGHT_MOTOR_2, LOW);

  digitalWrite(LEFT_MOTOR_1, HIGH);
  digitalWrite(LEFT_MOTOR_2, HIGH);
}


void rightMotorsOn() {

  digitalWrite(LEFT_MOTOR_1, LOW);
  digitalWrite(LEFT_MOTOR_2, LOW);

  digitalWrite(RIGHT_MOTOR_1, HIGH);
  digitalWrite(RIGHT_MOTOR_2, HIGH);
}


// ========================================
// SETUP
// ========================================

void setup() {

  Serial.begin(115200);

  // Motor GPIOs
  pinMode(LEFT_MOTOR_1, OUTPUT);
  pinMode(LEFT_MOTOR_2, OUTPUT);

  pinMode(RIGHT_MOTOR_1, OUTPUT);
  pinMode(RIGHT_MOTOR_2, OUTPUT);

  // Everything OFF at startup
  allOff();


  // ========================================
  // BLUETOOTH CLASSIC
  // ========================================

  SerialBT.begin("RIDEGUARD-ESP32");


  // ========================================
  // STARTUP MESSAGE
  // ========================================

  Serial.println();
  Serial.println("==============================");
  Serial.println("      RIDEGUARD ESP32");
  Serial.println("==============================");
  Serial.println("BLUETOOTH: CLASSIC SPP");
  Serial.println("DEVICE: RIDEGUARD-ESP32");
  Serial.println("STATUS: READY");
  Serial.println("Waiting for Bluetooth connection...");
  Serial.println("==============================");
}


// ========================================
// LOOP
// ========================================

void loop() {

  if (SerialBT.available()) {

    String command = SerialBT.readStringUntil('\n');

    command.trim();
    command.toUpperCase();

    Serial.print("BT COMMAND: ");
    Serial.println(command);


    if (command == "LEFT") {

      leftMotorsOn();

      Serial.println("LEFT HAPTIC ALERT");

    }

    else if (command == "RIGHT") {

      rightMotorsOn();

      Serial.println("RIGHT HAPTIC ALERT");

    }

    else if (command == "OFF") {

      allOff();

      Serial.println("ALL MOTORS OFF");

    }

    else {

      allOff();

      Serial.println("UNKNOWN COMMAND - MOTORS OFF");

    }
  }

  delay(10);
}