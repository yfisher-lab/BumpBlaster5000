#include "Arduino.h"
#include "Trigger.h"


Trigger::Trigger(int id, int to) {
    pin_id = id;
    timeout = to;
    
}

void Trigger::init() {
    pinMode(pin_id, OUTPUT);
    digitalWriteFast(pin_id, LOW);
    _state = false;
    _timestamp = millis();

}

void Trigger::trigger() {
    digitalWriteFast(pin_id, HIGH);
    _state = true;
    _timestamp = millis();
}

void Trigger::trigger_on_delay(int t) {
    delay_timer = millis();
    on_delay = true;
    delay = t;
}

void Trigger::check(int curr) {
    if (_state & (curr-_timestamp)>timeout) {
        digitalWriteFast(pin_id, LOW);
        state = false;
    }

    if (on_delay & ((curr-delay_timer)>delay)) {
        Trigger::trigger();
    }
}

bool Trigger::pin_state() {
    return _state;
}

int Trigger::get_timestamp() {
    return _timestamp;
}

  
