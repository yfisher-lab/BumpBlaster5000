#include "Arduino.h"
#include "Trigger.h"


Trigger::Trigger(int id, int to) {
    pin_id = id;
    timeout = to;
    
}

void Trigger::init() {
    pinMode(pin_id, OUTPUT);
    digitalWriteFast(pin_id, LOW);
    state = false;
    timestamp = millis();

}

void Trigger::trigger() {
    digitalWriteFast(pin_id, HIGH);
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
        digitalWriteFast(pin_id, LOW);
        state = false;
    }

    if (on_delay & ((curr-delay_timer)>delay)) {
        Trigger::trigger();
    }
}

bool Trigger::pin_state() {
    return state;
}

int Trigger::get_timestamp() {
    return timestamp;
}

  
