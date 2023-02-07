% Simple Bar stim

% 11 x 2 arena

npix = 8;
pattern = struct();
pattern.x_num = 12*npix; % 12 panels (1 virtual), 8 pixels per panels
pattern.y_num = 2; % no y control
pattern.num_panels = 22;
pattern.gs_val = 3; % 1 bit patterns
pattern.Pats = zeros(npix*2, 11*npix, 12*npix, 2);

img = im2double(rgb2gray(imread('street2.jpg')));
img = img(1:300,1:end);
img = img-min(min(img));
img_3bit = round(img/max(max(img))*7);
img_3bit_ds = imresize(img_3bit,[npix*2, 12*npix, 2]);


for frame_index = 1:12*npix
    frame = circshift(img_3bit_ds,frame_index,2);
    pattern.Pats(:,:,frame_index,1) = frame(1:end,1:11*npix);
end


pattern.Panel_map = [22 21 20 19 18 17 16 15 14 13 12;
                     11 10 9 8 7 6 5 4 3 2 1];

pattern.BitMapIndex = process_panel_map(pattern);

pattern.data = Make_pattern_vector(pattern);

% dir_name = 'C:\Users\fisherlab\Documents\repos\BumpBlaster5000\BumpBlaster5000\experiment_protocols';
% filename = [dir_name '\Pattern_bar_example_2pix'];

save(filename, 'pattern');