#include <FlashStorage.h> // Use the FlashStorage library instead of EEPROM

/*
2/25/2025 Geo Fratian Brown University
Modified on 8/12/2025 by Gemini

This code is used to read out from the Serial (sent via pyvisa) and move a stepper motor
a given amount of steps. It is used in conjuction with the python package PIEC.

Changes:
- Uses the FlashStorage library to store the motor's position in flash memory.
- On startup, it reads the last position from flash.
- Implements position limits (MIN_POS and MAX_POS).
- Checks if the startup position is within limits and sends an error if not.
- Prevents moves that would exceed the defined limits.
*/

// --- Pin Definitions ---
const byte directionPin = 6; // Pin that is wired to the Dir terminal
const byte stepPin = 7;      // Pin wired to Step terminal
const byte ledPin = 13;      // Indicator that motor is moving

// --- Stepper Motor & Position Settings ---
const int pulseWidthMicros = 20;     // Pulse width in microseconds
const int millisbetweenSteps = 50;   // Speed control: milliseconds between steps
const int MAX_POS = 540;            // <<< SET YOUR MAXIMUM ALLOWED POSITION HERE
const int MIN_POS = -540;           // <<< SET YOUR MINIMUM ALLOWED POSITION HERE

// --- Global Variables ---
int steps = 0; // Steps to move, received from Serial
int dir = 0;   // Direction to move, received from Serial
int pos = 0;   // Current position of the motor in steps

// --- Flash Storage Setup ---
// Create a FlashStorage object to hold our integer 'pos' variable.
// The first parameter is a name for the storage location.
FlashStorage(pos_storage, int);

void setup() {
  Serial.begin(115200);
  delay(2000); // Wait for Serial to initialize

  pinMode(directionPin, OUTPUT);
  pinMode(stepPin, OUTPUT);
  pinMode(ledPin, OUTPUT);

  // --- Flash Storage Initialization and Position Check ---
  // Read the last saved position from flash storage.
  pos = pos_storage.read();

  Serial.println("System Initialized.");
  Serial.println("Reading last position from Flash Storage...");

  // Check if the position read from flash is outside your defined limits.
  // This can happen if the device lost power mid-turn past a limit,
  // or if the flash has invalid data from the first-ever boot.
  if (pos > MAX_POS || pos < MIN_POS) {
    Serial.println("ERROR: Position on startup is past limits!");
    Serial.println("Last known position: " + String(pos));
    // You could add code here to lock operation until a reset command is received.
  } else {
    Serial.println("Position loaded successfully.");
  }

  Serial.println("Current Position: " + String(pos));
  Serial.println("Ready to receive commands...");
}


void loop() {
  if (Serial.available() > 0) {
    // Read the two integer values from the serial port
    steps = Serial.parseInt();
    dir = Serial.parseInt();

    // Clear any remaining characters (like newline) from the serial buffer
    while (Serial.available() > 0) {
      Serial.read();
    }

    // --- Command Handling ---

    // Special command: Reset position to zero
    if (dir == 9) {
      pos = 0;
      pos_storage.write(pos); // Save the new zero position to flash
      Serial.println("Position has been reset to 0.");
      return; // Exit this loop iteration
    }

    // Calculate the potential next position *before* actually moving
    int potential_pos = pos;
    if (dir == 1) { // Direction 1: Move forward
      potential_pos += steps;
    } else if (dir == 0) { // Direction 0: Move backward
      potential_pos -= steps;
    } else {
      Serial.println("ERROR: Invalid direction command. Use 0, 1, or 9.");
      return; // Exit without moving
    }

    // --- Limit Check ---
    // Check if the calculated move would go past your defined limits.
    if (potential_pos > MAX_POS) {
      Serial.println("ERROR: Move denied. Exceeds maximum limit of " + String(MAX_POS));
    } else if (potential_pos < MIN_POS) {
      Serial.println("ERROR: Move denied. Exceeds minimum limit of " + String(MIN_POS));
    } else {
      // If the move is within limits, proceed.
      pos = potential_pos; // Officially update the position variable
      
      // Set the direction pin accordingly
      if (dir == 1) {
        digitalWrite(directionPin, HIGH);
      } else {
        digitalWrite(directionPin, LOW);
      }
      
      moveSteps(); // Execute the physical move
      pos_storage.write(pos); // Save the new position to flash
    }
  }
}

// This function executes the physical stepping of the motor.
void moveSteps() {
  digitalWrite(ledPin, HIGH); // Turn on LED to indicate movement
  for (int n = 0; n < steps; n++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(pulseWidthMicros);
    digitalWrite(stepPin, LOW);
    delay(millisbetweenSteps);
  }
  digitalWrite(ledPin, LOW); // Turn off LED
  Serial.println("Move Completed! Current Position: " + String(pos));
}
