% Square stim

% 11 x 2 arena

npix = 8;
squareSize = 4;
pattern = struct();
pattern.x_num = 12*npix; % 12 panels (1 virtual), 8 pixels per panel
pattern.y_num = 1 + 2*npix / squareSize; % 2 panels, 8 pixels per panel, split evenly based on square size, and 1 dark
pattern.num_panels = 22;
pattern.gs_val = 1; % 1 bit patterns
pattern.Pats = zeros(npix*2, 11*npix, 12*npix, 1 + 2*npix/squareSize);

lastFrame = 11*npix-(squareSize-1);
elevations = 1:squareSize:2*npix;

for e = 1:1:(2*npix/squareSize)
    y = elevations(e):(elevations(e)+squareSize-1);

    for i = 1:lastFrame
        pattern.Pats(y, i:i+(squareSize-1), i, e) = 1;
    end
    
    for j = squareSize-1:-1:1
        pattern.Pats(y, end-j+1:end, lastFrame+1-(j-(squareSize-1)), e) = 1;
        pattern.Pats(y, 1:j, (end+(j-(squareSize-1))), e) = 1;
    end    
end

pattern.Pats = pattern.Pats(:,:,end:-1:1,:);
size(pattern.Pats)
pattern.Panel_map = [22 21 20 19 18 17 16 15 14 13 12;
                     11 10 9 8 7 6 5 4 3 2 1];

pattern.BitMapIndex = process_panel_map(pattern);

pattern.data = Make_pattern_vector(pattern);

dir_name = 'C:\Users\fisherlab\Documents\repos\BumpBlaster5000\BumpBlaster5000\experiment_protocols\G3_files';
filename = [dir_name '\Pattern_square_diff_elev_example_4pix'];

save(filename, 'pattern');



