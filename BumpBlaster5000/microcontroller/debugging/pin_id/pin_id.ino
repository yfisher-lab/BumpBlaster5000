const byte ft_frame_pin = 2;
const byte bk_scan_trig_pin = 3;
const byte bk_opto_trig_pin = 4;
const byte ft_dropped_frame_pin = 5;


#include <Wire.h>
#include <Adafruit_MCP4725.h>
Adafruit_MCP4725 heading_dac;
Adafruit_MCP4725 x_dac;
Adafruit_MCP4725 y_dac;
Adafruit_MCP4725 index_dac;
const int max_dac_val = 4095; // 4096 - 12-bit resolution

int counter = 0;

void setup() {
  // put your setup code here, to run once:
  pinMode(ft_frame_pin, OUTPUT);
  digitalWrite(ft_frame_pin, LOW);

  pinMode(bk_scan_trig_pin, OUTPUT);
  digitalWrite(bk_scan_trig_pin, LOW);

  pinMode(bk_opto_trig_pin,OUTPUT);
  digitalWrite(bk_opto_trig_pin,LOW);

  pinMode(ft_dropped_frame_pin, OUTPUT);
  digitalWrite(ft_dropped_frame_pin,LOW);

   // start DACs
  heading_dac.begin(0x62,&Wire);
  x_dac.begin(0x63,&Wire);
  y_dac.begin(0x62,&Wire1);
//  4th dac available for additional output
  index_dac.begin(0x63, &Wire1);
}

void loop() {
  // put your main code here, to run repeatedly:
//  digitalToggle(ft_frame_pin);
//  digitalToggle(bk_scan_trig_pin);
//  digitalToggle(bk_opto_trig_pin);
//  digitalToggle(ft_dropped_frame_pin);

//  heading_dac.setVoltage(counter, false);
//  x_dac.setVoltage(counter, false);
//  y_dac.setVoltage(counter, false);
  index_dac.setVoltage(counter,false);
  counter = (counter+1) % 4095;
  
  delay(1);

}
