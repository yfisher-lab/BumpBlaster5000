#ifndef FTHANDLER_H
#define FTHANDLER_H

#include "Arduino.h"
#include <Wire.h>
#include <Adafruit_MCP4725.h>
#include <math.h>
#include <cstring>


namespace ft {
    static bool closed_loop = false;
    static char chars[num_chars]; 
    static bool new_data = false;
    static int buff_ndx=0;
    static double heading;

    static double heading_offset;

    static int current_frame = 0;
    const int frame_pin = 2; 

    const int max_dac_val = 4095;
    const int num_cols = 26; 

    static int col;
    static int curr_time;

    Adafruit_MCP4725 heading_dac;
    Adafruit_MCP4725 index_dac;
    namespace dac_countdown {
        namespace heading {
            static bool on_delay = true;
            static int delay = 100;
            static int timestamp;
            static double heading;
        }

        namespace index {
            static bool on_delay = true;
            static int delay = 100;
            static int timestamp;
            static double index;
        }
    }
    
    void process_serial_data(){
        execute_col();
        if (closed_loop) {
            heading = fmod(ft_heading + heading_offset, 2*PI);
        } 
    }

    void update_dacs() {
        // check on delay timers
        curr_time = millis();
        if (dac_countdown::heading::on_delay ) {
            if (curr_time > (dac_countdown::heading::timestamp + dac_countdown::heading::delay)) {
                heading = dac_countdown::heading::heading
                dac_countdown::heading::on_delay = false;
            }
        }

        if (dac_countdown::index::on_delay) {
            if (curr_time > (dac_countdown::index::timestamp + dac_countdown::index::delay)) {
                index = dac_countdown::index::index;
                dac_countdown::index::on_delay = false;
            }
        }

        //  set dac vals
        heading_dac.setVoltage(int(max_dac_val * heading/2/PI ), false);
        index_dac.setVoltage(int(index), false);
    }


    void execute_col() {
        recv_data(); 
        if (ft_new_data == true) {
            update_col();
            col = (col+1) % num_cols; // keep track of columns in fictrack  
            new_data = false;
        }
    }

    void recv_data() { // receive Fictrac data
    
        static byte ndx = 0; // buffer index
        static char delimiter = ','; // column delimiter
        static char endline = '\n'; // endline character
        static char curr_byte; // current byte

        static _col_tmp;

        if (Serial.available() > 0) { // cannot use while(Serial.available()) because Teensy will read all 
            curr_byte = Serial.read(); 
            if ((curr_byte == endline)|(curr_byte==delimiter)) { // end of frame or new column      
                chars[ndx] = '\0'; // terminate the string
                ndx = 0; // restart buffer index
                new_data = true;   // cue new data

                if (curr_byte == endline) { // checks that columns are being counted correctly
                    int _col_tmp = col + 1;
                    if (_col_tmp != (num_cols)) {
                        col_ndx = num_cols-1;
                    }
                }
            }
            else {
                chars[ndx] = rc;
                ndx++;
                if (ndx >= num_chars) {
                    ndx = num_chars - 1;
                } 
            }
        }
    }

    void update_col() {

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
                break;
        }
    }

    void set_heading(int h) {
        heading = h;
    }

    void set_index(int i) {
        index = i;
    }

    void set_heading_offset(double o) {
        heading_offset = o;
    }

    void rotate_scene(double r) {
        heading_offset = fmod(heading_offset + r, 2*PI);
    }

    int get_index() {
        return index;
    }

    void set_index(int i) {
        index = i;
        // index = min(max(index, 0), max_dac_val);
    }

    void set_heading_on_delay(int t, double h){
        dac_countdown::heading::on_delay = true;
        dac_countdown::heading::delay = t;
        dac_countdown::heading::timestamp = millis();
        dac_countdown::heading::heading = h;
    }

    void set_index_on_delay(int t, int i ) {
        dac_countdown::index::on_delay = true;
        dac_countdown::index::delay = t;
        dac_countdown::index::timestamp = millis();
        dac_countdown::index::index = i;
    }

}

#endif