#include <SPI.h>

const int csPin = 10; // Connect to LTC1661 Pin 6 (CS/LD)

// LTC1661 Control Codes for Immediate Update
const uint16_t CMD_UPDATE_A = 0x9000; // Code 1001 (Load & Update A)
const uint16_t CMD_UPDATE_B = 0xA000; // Code 1010 (Load & Update B)

void setup() {
  pinMode(csPin, OUTPUT);
  digitalWrite(csPin, HIGH); // Ensure CS starts High
  
  SPI.begin();
  // Teensy 4.1 supports high speeds; 10MHz is well within LTC1661 limits
  Serial.begin(9600);
}

void loop() {
  // Example: Independently ramp DAC A
  for (int i = 0; i < 1024; i += 128) {
    writeDAC_A(i);
    Serial.print("DAC A set to: "); Serial.println(i);
    delay(500);
  }

  // Example: Independently set DAC B
  writeDAC_B(512); // Set to mid-scale (approx 1.65V if REF is 3.3V)
  Serial.println("DAC B set to mid-scale");
  delay(2000);
}

/**
 * Updates DAC A output immediately.
 * @param value 10-bit data (0 - 1023)
 */
void writeDAC_A(uint16_t value) {
  sendToLTC1661(CMD_UPDATE_A, value);
}

/**
 * Updates DAC B output immediately.
 * @param value 10-bit data (0 - 1023)
 */
void writeDAC_B(uint16_t value) {
  sendToLTC1661(CMD_UPDATE_B, value);
}

void sendToLTC1661(uint16_t command, uint16_t data) {
  // Mask data to 10 bits and shift left by 2 
  // to align with the LTC1661 16-bit word: [CMD][DATA][00]
  uint16_t packet = command | ((data & 0x03FF) << 2);

  SPI.beginTransaction(SPISettings(10000000, MSBFIRST, SPI_MODE0));
  digitalWrite(csPin, LOW);
  
  SPI.transfer16(packet);
  
  digitalWrite(csPin, HIGH); // Output updates on this rising edge
  SPI.endTransaction();
}