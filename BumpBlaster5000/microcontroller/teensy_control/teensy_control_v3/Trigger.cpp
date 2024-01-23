#include "Arduino.h"
#include "Trigger.h"


Trigger::Trigger() {
}



void Trigger::init(int id, int to, bool invert) {
    pin_id = id;
    timeout = to;
    inverted = invert;
    pinMode(pin_id, OUTPUT);
    if (inverted) {
        digitalWriteFast(pin_id, HIGH);
    } else {
        digitalWriteFast(pin_id, LOW);
    }
    
    state = false;
    timestamp = millis();

}

void Trigger::trigger() {
    if (inverted) {
        digitalWriteFast(pin_id, LOW);
    } else {
        digitalWriteFast(pin_id, HIGH);
    }
    
    state = true;
    timestamp = millis();
}

void Trigger::trigger_on_delay(int t) {
    delay_timer = millis();
    on_delay = true;
    delay = t;
}

void Trigger::check(int curr) {
    if (state & ((curr-timestamp)>timeout)) {
        if (inverted) {
            digitalWriteFast(pin_id, HIGH);
        } else {
            digitalWriteFast(pin_id, LOW);
        }
        
        state = false;
    }

    if (on_delay & ((curr-delay_timer)>delay)) {
        Trigger::trigger();
        on_delay = false;
    }
}

bool Trigger::pin_state() {
    return state;
}

int Trigger::get_timestamp() {
    return timestamp;
}

int Trigger::get_timeout() {
    return timeout;
}
  
