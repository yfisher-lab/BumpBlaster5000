#include "LTC1661.h"
#include <SPI.h>

// LTC1661 command nibbles (bits [15:12] of the 16-bit SPI word)
// 0x9 = Load DAC A input register and update both outputs immediately
// 0xA = Load DAC B input register and update both outputs immediately
static const uint16_t CMD_UPDATE_A = 0x9000;
static const uint16_t CMD_UPDATE_B = 0xA000;

LTC1661::LTC1661(int cs_pin, SPIClass& spi_port, float vref)
    : _cs_pin(cs_pin), _spi(&spi_port), _vref(vref) {}

void LTC1661::begin() {
    pinMode(_cs_pin, OUTPUT);
    digitalWrite(_cs_pin, HIGH);
    _spi->begin();
}

void LTC1661::setVoltage(int channel, float voltage) {
    if (channel < 0 || channel > 1) return;
    if (voltage < 0) voltage = 0;
    if (voltage > _vref) voltage = _vref;
    uint16_t value = (uint16_t)((voltage / _vref) * 1023.0f);
    writeDAC(channel, value);
}

void LTC1661::setDAC(int channel, uint16_t value) {
    if (channel < 0 || channel > 1) return;
    if (value > 1023) value = 1023;
    writeDAC(channel, value);
}

void LTC1661::writeDAC(int channel, uint16_t value) {
    // 16-bit word: [4-bit command][10-bit data][2 don't-care bits]
    uint16_t cmd  = (channel == 0) ? CMD_UPDATE_A : CMD_UPDATE_B;
    uint16_t word = cmd | ((value & 0x03FF) << 2);

    _spi->beginTransaction(SPISettings(10000000, MSBFIRST, SPI_MODE0));
    digitalWrite(_cs_pin, LOW);
    _spi->transfer16(word);
    digitalWrite(_cs_pin, HIGH); // output latches on rising CS edge
    _spi->endTransaction();
}