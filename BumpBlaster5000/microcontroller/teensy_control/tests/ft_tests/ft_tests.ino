#include "FTHandler.h"
//#include <cstring>
// const byte ft_frame_pin = 2; 
// FTHandler ft_handler(ft_frame_pin, &Serial);

// int curr_time;
// int low_time=0;
// int high_time=0;
#include <Wire.h>
#include <Adafruit_MCP4725.h>
#include <math.h>
#include <cstring>

int curr_time;
int last_rot_time=0;
double heading=0;
int ndx = 0;
void setup() {
  // put your setup code here, to run once:
  // FicTrac setup
  // FicTrac setup
  pinMode(ft::frame_pin,OUTPUT);
  digitalWrite(ft::frame_pin,LOW);
  

  // start DACs
  ft::heading_dac.begin(0x62,&Wire1);
  ft::index_dac.begin(0x63, &Wire1);
  ft::closed_loop=true;
}


void yield() {}
FASTRUN void loop() {
  // put your main code here, to run repeatedly:
  ft::process_serial_data();
  ft::update_dacs();
  
//  curr_time = millis();
//  if ((curr_time-last_rot_time)>500) {
////    ft::rotate_scene(PI/4);
//    last_rot_time = curr_time;
//
//    heading = fmod(heading+PI, 32*PI);
//    SerialUSB1.println(heading);
//    ndx = (ndx+1000)% 5000;
//    
//    ft::set_heading(heading);
//    ft::set_index_on_delay(100, ndx);
//  }
//
//  if ((curr_time-last_rot_time)>501) {
//    ft::set_heading_on_delay(100,PI);
//  }
  
}
