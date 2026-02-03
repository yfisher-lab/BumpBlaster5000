#include "LTC1661.h"
#include <SPI.h>

LTC1661::LTC1661(int cs_pin, float vref) : _cs_pin(cs_pin), _vref(vref) {}

void LTC1661::begin() {
    pinMode(_cs_pin, OUTPUT);
    digitalWrite(_cs_pin, HIGH);
    SPI.begin();
}

void LTC1661::setVoltage(int channel, float voltage) {
    if (channel < 0 || channel > 7) return;
    if (voltage < 0) voltage = 0;
    if (voltage > _vref) voltage = _vref;
    uint16_t value = (voltage / _vref) * 1023.0;
    writeDAC(channel, value);
}

void LTC1661::setDAC(int channel, uint16_t value) {
    if (channel < 0 || channel > 7) return;
    if (value > 1023) value = 1023;
    writeDAC(channel, value);
}

void LTC1661::writeDAC(int channel, uint16_t value) {
    uint16_t word = (value << 6) | (channel << 2);
    digitalWrite(_cs_pin, LOW);
    SPI.transfer16(word);
    digitalWrite(_cs_pin, HIGH);
}