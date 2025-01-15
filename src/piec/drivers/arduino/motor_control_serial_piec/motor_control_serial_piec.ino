/*
1/10/2025 Geo Fratian Brown University

This code is used to read out from the Serial (sent via pyvisa) and move a stepper motor 
a given amount of steps. It is used in conjuction with the python package PIEC
*/


byte directionPin = 6; // Pin that is wired to the Dir terminal
byte stepPin = 7; // Pin wired to Step terminal
byte ledPin = 13; //indicator that motor is moving
int steps = 0;
int dir = 0;

int pulseWidthMicros = 20;  // microseconds
int millisbetweenSteps = 50; // milliseconds - or try 1000 for slower steps basically speed
int pos = 0;

void setup() {
  Serial.begin(115200);
  delay(2000);

  pinMode(directionPin, OUTPUT);
  pinMode(stepPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
}


void loop() 
{
  if (Serial.available() > 0) {
    //Serial.println("new Data yippie");
    //Serial.write("Command Recieved\n");
      steps = Serial.parseInt();
      dir = Serial.parseInt();
      if (dir == 9){//set position to zero
        pos = 0;
      }
      if (dir == 99){//function to give out current position
        Serial.println(pos);
      }
      if (dir == 1){
        digitalWrite(directionPin, HIGH);
      }
      if (dir == 0){
        digitalWrite(directionPin, LOW);
      }
      moveSteps();
    }
  
  delay(1000);

}

void moveSteps()
{
  digitalWrite(ledPin, HIGH); //turn on LED indicator that steps will follow
  for(int n = 0; n < steps; n++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(pulseWidthMicros); // this line is probably unnecessary
    digitalWrite(stepPin, LOW);
    
    delay(millisbetweenSteps);

  }
  delay(100); //slight delay before turning off the LED
  digitalWrite(ledPin, LOW);

}
