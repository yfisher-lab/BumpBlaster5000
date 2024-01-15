#ifndef TRIGGER_H
#define TRIGGER_H

#include "Arduino.h"

class Trigger {
    int pin_id;
    bool state;
    int timestamp;
    int timeout; 
    
    int delay_timer;
    bool on_delay=false;
    int delay; 

    public:
        Trigger();
        void init(const int id, int to);
        void trigger();
        void trigger_on_delay(int t);
        void check(int curr);
        bool pin_state();
        int get_timestamp();
};




#endif 