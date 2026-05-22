

% 11 x 2 arena

npix = 8;
pattern = struct();
pattern.x_num = 12*npix; % 12 panels (1 virtual), 8 pixels per panels
pattern.y_num = 2; % no y control
pattern.num_panels = 22;
pattern.gs_val = 1; % 1 bit patterns
pattern.Pats = zeros(npix*2, 11*npix, 12*npix, 2);


H       = size(pattern.Pats, 1);
W_vis   = size(pattern.Pats, 2);   % 11*npix = 88
W_world = pattern.x_num;           % 12*npix = 96
T       = size(pattern.Pats, 3);   % 96

% world = ... (your sparse/dense/random world generation here)
world = zeros(H, W_world);

dot_density = 0.1;                  % fraction of world pixels that are ON
N = round(dot_density * H * W_world);

rng(1);                              % optional: fixed seed (remove/change if desired)
lin_idx = randperm(H * W_world, N);  % unique random pixels
world(lin_idx) = 1;


for i = 1:T
    start_col = i;  % always advance (1 px per frame)
    idx = mod((start_col-1) + (0:W_vis-1), W_world) + 1;
    pattern.Pats(:, :, i, 1) = world(:, idx);
end

pattern.Pats = pattern.Pats(:, :, end:-1:1, :);




% pattern.Panel_map = [22 21 20 19 18 17 16 15 14 13 12;
                    % 11 10 9 8 7 6 5 4 3 2 1];

% if test on behave rig
pattern.Panel_map = [02,04,06,08,10,12,14,16,18,20,22;
                     01,03,05,07,09,11,13,15,17,19,21];

pattern.BitMapIndex = process_panel_map(pattern);

pattern.data = Make_pattern_vector(pattern);

%dir_name = 'C:\Users\fisherlab\Documents\repos\BumpBlaster5000\BumpBlaster5000\experiment_protocols';
dir_name = 'C:\Users\fisherlab\Documents\GitHub\panels-patternsAndFunctions_behaviorRig\patterns\';
filename = [dir_name '\Pattern_TQ_dot_random_1pix'];

save(filename, 'pattern');
