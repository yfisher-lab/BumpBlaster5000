% Simple Bar stim  --> now: 2px ON / 5px OFF vertical grating (moving), continuous flow

% 11 x 2 arena
npix = 8;
pattern = struct();
pattern.x_num = 12*npix; % 12 panels (1 virtual), 8 pixels per panels
pattern.y_num = 2; % no y control
pattern.num_panels = 22;
pattern.gs_val = 1; % 1 bit patterns
pattern.Pats = zeros(npix*2, 11*npix, 12*npix, 2);

% ----- Moving vertical grating: 2 pixels ON, 5 pixels OFF -----
T = size(pattern.Pats, 3);  % = 12*npix = 96
W_vis = size(pattern.Pats, 2); % = 11*npix = 88

period = 7;   % 2 ON + 5 OFF
on_width = 2; % bright stripe width in pixels

for i = 1:T
    grating_cols = mod((1:W_vis) - i, period) < on_width;  % shifted each frame
    pattern.Pats(:, grating_cols, i, 1) = 1;
end

% Keep the same direction convention as your original pattern
pattern.Pats = pattern.Pats(:,:,end:-1:1,:);

% sanity check
size(pattern.Pats)


pattern.Panel_map = [22 21 20 19 18 17 16 15 14 13 12;
                     11 10 9 8 7 6 5 4 3 2 1];

% if test on behave rig
% pattern.Panel_map = [02,04,06,08,10,12,14,16,18,20,22;
                  %   01,03,05,07,09,11,13,15,17,19,21];

pattern.BitMapIndex = process_panel_map(pattern);
pattern.data = Make_pattern_vector(pattern);


%dir_name = 'C:\Users\fisherlab\Documents\repos\BumpBlaster5000\BumpBlaster5000\experiment_protocols';
dir_name = 'C:\Users\fisherlab\Documents\GitHub\panels-patternsAndFunctions_behaviorRig\patterns';
filename = [dir_name '\Pattern_vertical_grating_2on5off_smaug'];

save(filename, 'pattern');
