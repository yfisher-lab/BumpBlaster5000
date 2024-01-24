#ifndef FTHANDLER_H
#define FTHANDLER_H

#include "Arduino.h"

#include <Adafruit_BusIO_Register.h>
#include <Adafruit_I2CDevice.h>
#include <Adafruit_MCP4725.h>
#include <Wire.h>
#include <math.h>
#include <cstring>
#include <algorithm>
using namespace std;

const int num_chars = 256;

struct dac_countdown {
    bool on_delay = false;
    int delay;
    int timestamp;
    double val;
};

class FTHandler {
    bool closed_loop = true;
    char chars[num_chars]; 
    bool new_data = false;

    int h_addr;
    int i_addr;
    double heading;
    bool new_heading;
    dac_countdown heading_countdown;
    double ft_heading;
    int index;
    bool new_index;
    dac_countdown index_countdown;

    double heading_offset=0;

    int current_frame = 0;
    int frame_pin;

    int max_dac_val = 4095;
    int num_cols = 26; 

    int col=0;
    int curr_time;

    Stream& srl;  

    Adafruit_MCP4725 heading_dac;
    Adafruit_MCP4725 index_dac;

    
    void recv_data();
    void update_col();
    void execute_col();

    public: 
        FTHandler(Stream& srl_ref);
        void init(int f_pin, TwoWire* w1, uint8_t addr1, TwoWire* w2, 
                    uint8_t addr2);
        
        void process_srl_data();
        void update_dacs();

        void set_heading(int h);

        void set_index(int i);

        void set_heading_offset(double o);

        void rotate_scene(double r);
        int get_index(); 

        void set_heading_on_delay(int t, double h);

        void set_index_on_delay(int t, int i );


};

// namespace ft {



//     static bool closed_loop = true;
//     static char chars[num_chars]; 
//     static bool new_data = false;
    
//     static double heading;
//     static bool new_heading;
//     static double ft_heading;
//     static int index;
//     static bool new_index;

//     static double heading_offset=0;

//     static int current_frame = 0;
//     const int frame_pin = 2; 

//     const int max_dac_val = 4095;
//     const int num_cols = 26; 

//     static int col;
//     static int curr_time;

//     Adafruit_MCP4725 heading_dac;
//     Adafruit_MCP4725 index_dac;
//     namespace dac_countdown {
//         namespace heading {
//             static bool on_delay = true;
//             static int delay = 100;
//             static int timestamp;
//             static double heading;
//         }

//         namespace index {
//             static bool on_delay = true;
//             static int delay = 100;
//             static int timestamp;
//             static double index;
            
//         }
//     }

//      void recv_data() { // receive Fictrac data
    
//         static byte ndx = 0; // buffer index
//         static char delimiter = ','; // column delimiter
//         static char endline = '\n'; // endline character
//         static char curr_byte; // current byte

//         static int _col_tmp;

//         if (Serial.available() > 0) { // cannot use while(Serial.available()) because Teensy will read all 
//             curr_byte = Serial.read(); 
//             if ((curr_byte == endline)|(curr_byte==delimiter)) { // end of frame or new column      
//                 chars[ndx] = '\0'; // terminate the string
//                 ndx = 0; // restart buffer index
//                 new_data = true;   // cue new data

//                 if (curr_byte == endline) { // checks that columns are being counted correctly
//                     _col_tmp = col + 1;
//                     if (_col_tmp != (num_cols)) {
//                         col = num_cols-1;
//                     }
//                 }
//             }
//             else {
//                 chars[ndx] = curr_byte;
//                 ndx++;
//                 if (ndx >= num_chars) {
//                     ndx = num_chars - 1;
//                 } 
//             }
//         }
//     }

//     void update_col() {

//         // switch case statement for variables of interest
//         switch (col) {
            
//             case 0: // new FicTrac frame
//                 // flip ft pin high
//                 digitalWriteFast(frame_pin,HIGH);
//                 break;

//             case 1: // frame counter
//                 current_frame = atoi(chars);
//                 break;

//             case 17: // heading 
//                 // flip ft pin low 
//                 digitalWriteFast(frame_pin,LOW);

//                 // update heading pin
//                 ft_heading = atof(chars) + PI;
//                 new_heading = true;
//                 break;
//         }
//     }
    
//     void execute_col() {
//         ft::recv_data(); 
//         if (new_data == true) {
//             ft::update_col();
//             col = (col+1) % num_cols; // keep track of columns in fictrack  
//             new_data = false;
//         }
//     }
    
//     void process_serial_data(){
//         ft::execute_col();
//         if (closed_loop) {
//             heading = fmod(ft_heading + heading_offset, 2*PI);
//         } 
//     }

//     void update_dacs() {
//         // check on delay timers
//         curr_time = millis();
//         if (dac_countdown::heading::on_delay ) {
//             if (curr_time > (dac_countdown::heading::timestamp + dac_countdown::heading::delay)) {
//                 heading = dac_countdown::heading::heading;
//                 dac_countdown::heading::on_delay = false;
//                 new_heading = true;
//             }
//         }
// //
//         if (dac_countdown::index::on_delay) {
//             if (curr_time > (dac_countdown::index::timestamp + dac_countdown::index::delay)) {
//                 index = dac_countdown::index::index;
//                 dac_countdown::index::on_delay = false;
//                 new_index = true;
//             }
//         }

// ////          set dac vals
//         if (new_heading){
//           heading_dac.setVoltage(int(max_dac_val * heading/2/PI), false);
//           new_heading = false;
//         }
//         if (new_index) {
//           index_dac.setVoltage(int(index), false);
//           new_index = false;
//         }

//     }

//     void set_heading(int h) {
//         heading = fmod(h, 2*PI);
//         new_heading = true;
//     }

//     void set_index(int i) {
//         index = std::max(std::min(i, max_dac_val),0);
//         new_index = true;
//     }

//     void set_heading_offset(double o) {
//         heading_offset = o;
//     }

//     void rotate_scene(double r) {
//         heading_offset = fmod(heading_offset + r, 2*PI);
//     }

//     int get_index() {
//         return index;
//     }

//     void set_heading_on_delay(int t, double h){
//         dac_countdown::heading::on_delay = true;
//         dac_countdown::heading::delay = t;
//         dac_countdown::heading::timestamp = millis();
//         dac_countdown::heading::heading = fmod(h, 2*PI);
//     }

//     void set_index_on_delay(int t, int i ) {
//         dac_countdown::index::on_delay = true;
//         dac_countdown::index::delay = t;
//         dac_countdown::index::timestamp = millis();
//         dac_countdown::index::index = std::max(std::min(i, max_dac_val),0);
//     }

// }


#endif
