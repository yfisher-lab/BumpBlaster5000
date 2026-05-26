// triangle_wave_test.ino
//
// Outputs a triangle wave on both LTC1661 DAC channels simultaneously,
// and toggles digital pins 2-5 every 2 seconds.
//
// Wiring (SPI1):
//   Pin 26 -> DIN  (MOSI)
//   Pin 27 -> CLK  (SCK)
//   Pin 10 -> CS   (chip select)
//   VREF   -> 5V reference
//   VDD    -> 5V, GND -> GND

#include <SPI.h>
#include "LTC1661.h"

// --- configuration ---------------------------------------------------

LTC1661 dac(10, SPI1);         // CS pin 10, SPI port 1

const int   TOGGLE_PINS[]    = {2, 3, 4, 5};
const int   NUM_TOGGLE_PINS  = 4;
const unsigned long TOGGLE_MS = 2000;   // pin flip interval (ms)

// Triangle wave: step every WAVE_STEP_US microseconds.
// Full cycle = 2 * 1023 steps.
// WAVE_STEP_US = 977 => ~2 second period (1 Hz triangle wave).
const unsigned long WAVE_STEP_US = 977;

// --- state -----------------------------------------------------------

int  dac_value   = 0;
int  dac_dir     = 1;          // +1 = rising, -1 = falling
bool pin_state   = false;

unsigned long last_wave_us   = 0;
unsigned long last_toggle_ms = 0;

// ---------------------------------------------------------------------

void setup() {
    Serial.begin(9600);

    dac.begin();

    for (int i = 0; i < NUM_TOGGLE_PINS; i++) {
        pinMode(TOGGLE_PINS[i], OUTPUT);
        digitalWrite(TOGGLE_PINS[i], LOW);
    }

    last_wave_us   = micros();
    last_toggle_ms = millis();

    Serial.println("triangle_wave_test started");
    Serial.println("DAC A & B: 1 Hz triangle wave (0-1023)");
    Serial.println("Pins 2-5: toggle every 2 s");
}

void loop() {

    // --- triangle wave (non-blocking) --------------------------------
    unsigned long now_us = micros();
    if (now_us - last_wave_us >= WAVE_STEP_US) {
        last_wave_us = now_us;

        dac.setDAC(0, (uint16_t)dac_value);   // DAC A — heading channel
        dac.setDAC(1, (uint16_t)dac_value);   // DAC B — index channel

        dac_value += dac_dir;
        if (dac_value >= 1023) { dac_value = 1023; dac_dir = -1; }
        if (dac_value <= 0)    { dac_value = 0;    dac_dir =  1; }
    }

    // --- pin toggle (non-blocking) -----------------------------------
    unsigned long now_ms = millis();
    if (now_ms - last_toggle_ms >= TOGGLE_MS) {
        last_toggle_ms = now_ms;
        pin_state = !pin_state;

        for (int i = 0; i < NUM_TOGGLE_PINS; i++) {
            digitalWrite(TOGGLE_PINS[i], pin_state ? HIGH : LOW);
        }

        Serial.print("pins 2-5 -> ");
        Serial.println(pin_state ? "HIGH" : "LOW");
    }
}
