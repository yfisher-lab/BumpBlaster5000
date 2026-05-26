#ifndef LTC1661_H
#define LTC1661_H

#include <Arduino.h>
#include <SPI.h>

class LTC1661 {
public:
    // spi_port defaults to SPI (port 0, pins 11/12/13).
    // Pass SPI1 for port 1 (pins 26/1/27) or SPI2 for port 2.
    LTC1661(int cs_pin, SPIClass& spi_port = SPI, float vref = 5.0);
    void begin();
    void setVoltage(int channel, float voltage);
    void setDAC(int channel, uint16_t value);

private:
    int _cs_pin;
    float _vref;
    SPIClass* _spi;  // pointer so LTC1661 remains copyable/assignable
    void writeDAC(int channel, uint16_t value);
};

#endif