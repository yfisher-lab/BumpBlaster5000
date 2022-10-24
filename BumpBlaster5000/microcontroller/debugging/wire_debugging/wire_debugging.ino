
#include <Wire.h>
#include <Adafruit_MCP4725.h>
Adafruit_MCP4725 heading_dac;
Adafruit_MCP4725 heading2_dac;
Adafruit_MCP4725 x_dac;
Adafruit_MCP4725 y_dac;


void setup() {
  // put your setup code here, to run once:
  // start DACs
  heading_dac.begin(0x62  ,&Wire);
  heading2_dac.begin(0x63  ,&Wire);
  x_dac.begin(0x62,&Wire1);
  y_dac.begin(0x63,&Wire1);

}

FASTRUN void loop() {
  // put your main code here, to run repeatedly:

  uint32_t counter;
////    // Run through the full 12-bit scale for a triangle wave
    for (counter = 0; counter < 4095; counter++)
    {
//      digitalWrite(12, HIGH);
      heading_dac.setVoltage(counter, false);
      heading2_dac.setVoltage(counter, false);
      x_dac.setVoltage(counter, false);
      y_dac.setVoltage(counter, false);
//      delay(1);
      

      
    }
    for (counter = 4095; counter > 0; counter--)
    {
      heading_dac.setVoltage(counter, false);
      heading2_dac.setVoltage(counter, false);
      x_dac.setVoltage(counter, false);
      y_dac.setVoltage(counter, false);
//      delay(1);
    }

}
