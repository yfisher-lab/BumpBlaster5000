#ifndef TRIGGER_H
#define TRIGGER_H

#include "Arduino.h"

class Trigger {
    int pin_id;
    bool state;
    int timestamp;
    int timeout; 
    bool inverted;
    
    int delay_timer;
    bool on_delay=false;
    int delay; 

    public:
        Trigger();
        void init(int id, int to, bool invert);
        void trigger();
        void trigger_on_delay(int t);
        void check(int curr);
        bool pin_state();
        int get_timestamp();
        int get_timeout();
};




#endif 
