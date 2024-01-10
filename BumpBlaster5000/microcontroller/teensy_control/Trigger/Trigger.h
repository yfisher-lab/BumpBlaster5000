#ifndef TRIGGER_H
#define TRIGGER_H

#include "Arduino.h"

class Trigger {
    int pin_id;
    bool _state;
    int _timestamp;
    int timeout; 
    
    public:
        Trigger(int id, int to);
        void init();
        void trigger();
        void check();
        bool pin_state();
        int get_timestamp();
}




#endif 