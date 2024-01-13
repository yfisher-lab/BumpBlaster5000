#include "FTHandler.h"
#include <cstring>
const byte ft_frame_pin = 2; 
FTHandler ft_handler(ft_frame_pin, &Serial);

int curr_time;
int low_time=0;
int high_time=0;

void setup() {
  // put your setup code here, to run once:
  // FicTrac setup
  ft_handler.init(0x62, &Wire1, 0x63, &Wire1);
}

void yield() {}
FASTRUN void loop() {
  // put your main code here, to run repeatedly:
  ft_handler.process_serial_data();
  ft_handler.update_dacs();
  curr_time = millis();
//  if ((curr_time-high_time)>1000) {
//
////    ft_handler.rotate_scene(PI/8);
////    ft_handler.set_heading_on_delay(400, 2*PI);
////    ft_handler.set_index_on_delay(200, 4095);
//    high_time = millis();
////    SerialUSB1.println(ft_handler.get_index());
//  }
////  if ((curr_time-high_time)>500) {
////    ft_handler.set_heading(0);
////    ft_handler.set_index(0);
////  }
////  ft_handler.set_heading_on_delay(300, 2*PI);
//  ft_handler.set_index(0);
//  ft_handler.update_dacs();
//  delay(1000);
//  ft_handler.set_heading(0);
//  ft_handler.set_index(4095);
//  ft_handler.update_dacs();
//  delay(1000);
//  
  
}
