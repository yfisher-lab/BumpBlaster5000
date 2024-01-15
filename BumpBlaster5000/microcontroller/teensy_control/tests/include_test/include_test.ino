// #include "C:\\Users\\fisherlab\\Documents\\repos\\BumpBlaster5000\\BumpBlaster5000\\microcontroller\\teensy_control\\FTHandler\\FTHandler.h"
// #include "C:\\Users\\fisherlab\\Documents\\repos\\BumpBlaster5000\\BumpBlaster5000\\microcontroller\\teensy_control\\Trigger\\Trigger.h"
// #include "Trigger.h"


namespace n1 {
  static int a=0;
}
// Trigger trig;
const int num_chr = 256;
struct test {
    char chars[num_chr];
    bool new_state;

};
test _test;

void setup() {
  // put your setup code here, to run once:
  // trig.init(3,10);
  n1::a = 1;

}

void loop() {
  // put your main code here, to run repeatedly:
  // trig.trigger_on_delay(10);
}


