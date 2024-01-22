#include "FTHandler.h"
#include <cstring>
// const byte ft_frame_pin = 2; 
// FTHandler ft_handler(ft_frame_pin, &Serial);

// int curr_time;
// int low_time=0;
// int high_time=0;

void setup() {
  // put your setup code here, to run once:
  // FicTrac setup
  // FicTrac setup
  pinMode(ft::frame_pin,OUTPUT);
  digitalWrite(ft::frame_pin,LOW);
  

  // start DACs
  ft::heading_dac.begin(0x62,&Wire1);
  ft::index_dac.begin(0x63, &Wire1);

}

void yield() {}
FASTRUN void loop() {
  // put your main code here, to run repeatedly:
 
}
