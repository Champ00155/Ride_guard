#define MOTOR_LEFT 14
#define MOTOR_RIGHT 4

void setup() {
  pinMode(MOTOR_LEFT, OUTPUT);
  pinMode(MOTOR_RIGHT, OUTPUT);

  // Start OFF
  digitalWrite(MOTOR_LEFT, LOW);
  digitalWrite(MOTOR_RIGHT, LOW);
}

void loop() {
  // Both motors ON
  digitalWrite(MOTOR_LEFT, HIGH);
  digitalWrite(MOTOR_RIGHT, LOW);

  delay(2000);  // ON for 2 seconds

  // Both motors OFF
  digitalWrite(MOTOR_LEFT, LOW);
  digitalWrite(MOTOR_RIGHT, HIGH);

  delay(2000);  // OFF for 2 seconds
}