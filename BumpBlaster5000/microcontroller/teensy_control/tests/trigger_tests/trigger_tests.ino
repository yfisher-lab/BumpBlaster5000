#include "Trigger.h"

struct {
    Trigger trig; 
    bool is_scanning=false;
} bk_scan;



Trigger bk_opto_trig; 
Trigger pump_trig; 

int curr_time;
int last_flip;

void setup() {
  // put your setup code here, to run once:
  bk_scan.is_scanning = false;
  // Bruker setup
  bk_scan.trig.init(3, 10, false);
  bk_opto_trig.init(4, 10, false);
  
  // Pump trigger setup
  pump_trig.init(5, 10, true);

//  last_flip = millis();
}

void yield() {}

FASTRUN void loop() {
  // put your main code here, to run repeatedly:

  curr_time = millis();
  if ((curr_time-last_flip)>1000) {

    pump_trig.trigger();
    bk_scan.trig.trigger_on_delay(100);
    bk_opto_trig.trigger_on_delay(200);
    last_flip = millis();
    // Serial.println(pump_trig.get_timestamp());
  }

  pump_trig.check(curr_time);
  bk_scan.trig.check(curr_time);
  bk_opto_trig.check(curr_time);
  
}
