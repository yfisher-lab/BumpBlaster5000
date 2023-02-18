% Simple Bar stim

% 11 x 2 arena

npix = 8;
pattern = struct();
pattern.x_num = 12*npix; % 12 panels (1 virtual), 8 pixels per panels
pattern.y_num = 2; % no y control
pattern.num_panels = 22;
pattern.gs_val = 1; % 1 bit patterns
pattern.Pats = zeros(npix*2, 11*npix, 12*npix, 2);

for i = 1:11*npix-1
    pattern.Pats(:, i:i+7, i, 1) = 1;
end

pattern.Pats(:,1:8,11*npix:end,1)=1;


pattern.Pats = pattern.Pats(:,:,end:-1:1,:);
size(pattern.Pats)
pattern.Panel_map = [22 21 20 19 18 17 16 15 14 13 12;
                     11 10 9 8 7 6 5 4 3 2 1];

pattern.BitMapIndex = process_panel_map(pattern);

pattern.data = Make_pattern_vector(pattern);

dir_name = 'C:\Users\fisherlab\Documents\repos\BumpBlaster5000\BumpBlaster5000\experiment_protocols';
filename = [dir_name '\Pattern_4pix_bar'];

save(filename, 'pattern');
