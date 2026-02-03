#ifndef LTC1661_H
#define LTC1661_H

#include <Arduino.h>

class LTC1661 {
public:
    LTC1661(int cs_pin, float vref = 5.0);
    void begin();
    void setVoltage(int channel, float voltage);
    void setDAC(int channel, uint16_t value);

private:
    int _cs_pin;
    float _vref;
    void writeDAC(int channel, uint16_t value);
};

#endif