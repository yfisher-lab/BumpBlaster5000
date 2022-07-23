import itertools

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

pg.setConfigOptions(imageAxisOrder='row-major')

## Create image to display
arr = np.ones((100, 100), dtype=float)
arr[45:55, 45:55] = 0
arr[25, :] = 5
arr[:, 25] = 5
arr[75, :] = 5
arr[:, 75] = 5
arr[50, :] = 10
arr[:, 50] = 10
arr += np.sin(np.linspace(0, 20, 100)).reshape(1, 100)
arr += np.random.normal(size=(100,100))


## create GUI
app = QtGui.QApplication([])
w = pg.GraphicsLayoutWidget(show=True, size=(1000,800), border=True)
w.setWindowTitle('pyqtgraph example: ROI Examples')

text = """Data Selection From Image.<br>\n
Drag an ROI or its handles to update the selected image.<br>
Hold CTRL while dragging to snap to pixel boundaries<br>
and 15-degree rotation angles.
"""
w1 = w.addLayout(row=0, col=0)
label1 = w1.addLabel(text, row=0, col=0)
v1a = w1.addViewBox(row=1, col=0, lockAspect=True)
v1b = w1.addViewBox(row=2, col=0, lockAspect=True)
img1a = pg.ImageItem(arr)
v1a.addItem(img1a)
img1b = pg.ImageItem()
v1b.addItem(img1b)
v1a.disableAutoRange('xy')
v1b.disableAutoRange('xy')
v1a.autoRange()
v1b.autoRange()

rois = []
# outer_roi
rois.append(pg.EllipseROI([10, 10], [50, 50], pen=(3, 9), scaleSnap=True, translateSnap=True, rotatable=False))
# inner_roi
rois.append(pg.EllipseROI([25, 25], [10, 10], pen=(3, 9), scaleSnap=True, translateSnap=True, rotatable=False))

def update(roi):
    print(roi.pos()[0],roi.size())
    # print("getArraySlice", rois[0].getArraySlice(arr, img1a))
    # img1b.setImage(_donut_mask(rois[0],rois[1], np.ones(arr.shape), img1a))
    # img1b.setColorMap(pg.colormap.get('hsv',source='matplotlib'))
    img1b.setImage(make_masks(rois[0], rois[1], np.ones(arr.shape), img1a)[1])
    print((make_masks(rois[0], rois[1], np.ones(arr.shape), img1a)[1]>0).sum())
    roi.translatable=False
    roi.resizeable = False
    for h in roi.getHandles():
        roi.removeHandle(h)
    # print(roi.getHandles())
    # v1b.autoRange()
    # img1b.setImage(rois[0].getArrayRegion(arr, img1a)-rois[1].getArrayRegion(arr, img1a),
    #                levels = (0, arr.max()))
    v1b.autoRange()

for roi in rois:
    roi.sigRegionChanged.connect(update)
    v1a.addItem(roi)

def phase_calc(nrows,ncols, center = None):
    phase_mask = np.zeros([nrows,ncols])

    if center is None:
        center = (int(nrows/2),int(ncols/2))

    for row, col in itertools.product(range(nrows),range(ncols)):
        phase_mask[row, col] = np.arctan2(col-center[1], row-center[0])

    return phase_mask

def _donut_mask(outer_roi, inner_roi, ch_arr, ch_img):
    outer_mask = 1.*(outer_roi.getArrayRegion(ch_arr, ch_img)>0)
    # print('outer_mask shape',outer_mask.shape)
    _inner_mask = 1. * (inner_roi.getArrayRegion(ch_arr, ch_img) > 0)
    # print('inner_mask shape', _inner_mask.shape)
    # top left corner
    print('positions', outer_roi.pos(), inner_roi.pos())
    inner_mask_rel_pos = (int(inner_roi.pos()[1] - outer_roi.pos()[1]),
                          int(inner_roi.pos()[0] - outer_roi.pos()[0]))
    # inner_mask_rel_pos = (outer_mask.shape[0] - int(inner_roi.pos()[1] - outer_roi.pos()[1]),
    #                       int(inner_roi.pos()[0] - outer_roi.pos()[0]))
    print('inner_mask_rel_pos', inner_mask_rel_pos)
    inner_mask = np.zeros(outer_mask.shape)
    inner_mask[inner_mask_rel_pos[0]:inner_mask_rel_pos[0] + _inner_mask.shape[0],
    inner_mask_rel_pos[1]:inner_mask_rel_pos[1] + _inner_mask.shape[1]] = _inner_mask

    # EB shape
    donut_mask = 1. * ((outer_mask - inner_mask) > 1E-5)
    donut_mask[donut_mask==0]=np.nan
    return donut_mask

def make_masks(outer_roi, inner_roi, ch_arr, ch_img):

    donut_mask = _donut_mask(outer_roi, inner_roi, ch_arr, ch_img)
    # get phase of each pixel, assuming center of image patch is origin
    phase_mask = phase_calc(*donut_mask.shape)*donut_mask

    return donut_mask, phase_mask


def cart2pol(x,y):
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y,x)
    return rho, phi

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y

# @jit
def bump_vec(phase_mask, dff_img):
    x, y = pol2cart(dff_img, phase_mask)
    return cart2pol(x.sum(), y.sum())


# for live z scoring fluorescence
def update_mean_var(count, mean, M2, new_value):
    count +=1
    delta = new_value - mean
    mean += delta / count
    M2 += delta * (new_value - mean)
    return count, mean, M2, np.sqrt(M2/count) # std

# running smoothed floor ceil calculation
def running_baseline(buff, width = 10):
    return np.percentile(np.gaussian_filter1d(buff,width, axis=1),5,axis=1)







#
#TODO: make subfunction that only uses np arrays and uses @jit decorator
# def get_wedge_masks(outer_roi, inner_roi, ch_arr, ch_img, resolution = 16 ):
#     # .pos() returns (x,y) relative to bottom left corner
#     #   size() also returs (x,y)
#
#     outer_mask = outer_roi.getArrayRegion(ch_arr, ch_img)
#     # outer_mask[outer_mask==0] = np.nan
#     # get phase of each pixel, assuming center of image patch is origin
#     phase_mask = phase_calc(*outer_mask.shape)
#
#
#     _inner_mask = 1.*(inner_roi.getArrayRegion(ch_arr, ch_img) > 0)
#     # top left corner
#     inner_mask_rel_pos = (outer_mask.shape[0] - int(outer_roi.pos()[1] - inner_roi.pos()[1]) - _inner_mask.shape[0],
#                           outer_mask.shape[1] - int(outer_roi.pos()[0] - inner_roi.pos()[0]) )
#
#     inner_mask = np.zeros(outer_mask.shape)
#     inner_mask[inner_mask_rel_pos[0]:inner_mask_rel_pos[0] + _inner_mask.shape[0],
#                inner_mask_rel_pos[1]:inner_mask_rel_pos[1] + _inner_mask.shape[1]] = _inner_mask
#
#     # EB shape
#     donut_mask = 1.*((outer_mask-inner_mask) > 1E-5)
#     phase_mask = phase_mask*donut_mask
#
#     r = dff(donut_mask*outer_roi.getArrayRegion(ch_arr, ch_img)),phase_mask
#
#     # compare speed of averaging then doing mean vs this method
#     #     wedge_masks = np.zeros([*donut_mask.shape, resolution])
#     #     bin_edges = np.linspace(0,2*np.pi,num=resolution+1)
#     #
#     #     bin_centers = []
#     #     for itr, (ledge, redge)  in enumerate(zip(bin_edges[:-1].tolist(), bin_edges[1:].tolist())):
#     #         wedge_masks[:,:,itr] = 1.*(donut_mask * (phase_mask>=ledge) * (phase_mask<redge))
#     #         bin_centers.append(ledge+redge)
#     #
#     #     return wedge_masks, bin_centers
#     #
#
#




# def apply_wedge_masks(wedge_masks, ch_image):
#
#     resolution = wedge_masks.shape[-1]
#
#     for w in range(wedge_masks.shape[-1]):




if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()