#include "Arduino.h"
#include "FTHandler.h"


FTHandler::FTHandler(int f_pin, Stream *srl_port) { // add serial line reference to constructor? 
    frame_pin = f_pin;
    current_frame = 0;
    closed_loop = true;
    new_data = false;
    col = 0;
    Srl = srl_port;
    
}
        
void FTHandler::init(uint8_t h_dac_addr, TwoWire *h_dac_wire, 
                    int i_dac_addr, TwoWire *i_dac_wire) {
    
    
    heading_dac.begin(h_dac_addr, h_dac_wire);
    index_dac.begin(i_dac_addr, h_dac_wire);

    heading_offset = 0;

    pinMode(frame_pin, OUTPUT);
    digitalWriteFast(frame_pin, LOW);

}

void FTHandler::receive_srl_data() {
    static int _col;

    if (Srl->available() > 0) { // cannot use while(Serial.available()) because Teensy will read all 
        curr_byte = Srl->read(); 
        if ((curr_byte == endline)|(curr_byte==delimiter)) { // end of frame or new column      
          chars[buffer_ndx] = '\0'; // terminate the string
          buffer_ndx = 0; // restart buffer index
          
          if (curr_byte == endline) { // checks that columns are being counted correctly
            _col = col+1;

            if (_col != (num_cols)) {
              // print error to serial port 
              //digitalToggle(ft_dropped_frame_pin);
              col = num_cols-1;
            }
          }
          new_data = true;   // cue new data

        }
        else {
          chars[buffer_ndx] = curr_byte;
          buffer_ndx++;
          if (buffer_ndx >= num_chars) {
              buffer_ndx = num_chars - 1;
          } 
          new_data = false;
        }
        new_data = false;
    }
}

void FTHandler::update_col() {
    if (new_data) {
        FTHandler::execute_col();
        col = (col+1) % num_cols;
    }
}

void FTHandler::execute_col() {
  // switch case statement for variables of interest
  switch (col) {
    
    case 0: // new FicTrac frame
      // flip ft pin high
      digitalWriteFast(frame_pin,HIGH);
      break;

    case 1: // frame counter
      current_frame = atoi(chars);
      break;

    case 17: // heading 
      // flip ft pin low 
      digitalWriteFast(frame_pin,LOW);

      // update heading pin
      ft_heading = atof(chars) + PI;
      
  }

}

void FTHandler::process_serial_data(){
    FTHandler::receive_srl_data();
    FTHandler::update_col();

    if (closed_loop) {
        heading = fmod(ft_heading + heading_offset, 2*PI);
    } 
}

void FTHandler::update_dacs() {
    // check on delay timers
    curr_time = millis();
    if (heading_on_delay & (curr_time>(heading_delay_timestamp + heading_delay))) {
        FTHandler::set_heading(delayed_heading_val);
    }
    if (index_on_delay & (curr_time>(index_delay_timestamp + index_delay))) {
        FTHandler::set_index(delayed_index_val);
    }


    //  set dac vals
    heading_dac.setVoltage(int(max_dac_val * heading ), false);
    index_dac.setVoltage(int(index), false);

}

void FTHandler::set_heading(double h) {
    heading = h;
}

double FTHandler::get_heading() {
    return heading;
}

void FTHandler::set_heading_offset(double o) {
    heading_offset = o;
}

void FTHandler::rotate_scene(double r) {
    heading_offset = fmod(heading_offset + r, 2*PI);
}

int FTHandler::get_index() {
    return index;
}

void FTHandler::set_index(int i) {
    index = index+i;
    index = min(max(index, 0), max_dac_val);
}

void FTHandler::set_heading_on_delay(int t, double h){
    heading_on_delay = true;
    heading_delay = t;
    heading_delay_timestamp = millis();
    delayed_heading_val = h;
}

void FTHandler::set_index_on_delay(int t, int i ) {
    index_on_delay = true;
    index_delay = t;
    index_delay_timestamp = millis();
    delayed_index_val = i; 
}