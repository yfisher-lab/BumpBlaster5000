import PyCapture2 as pycap

bus = PyCapture2.BusManager
uid = bus.getCameraFromSerialNumber(13192198)
c = PyCapture2.Camera()
c.connect(guid)
c.startCapture()
img = c.retrieveBuffer()
cv_image = np.array(img.getData(), dtype='uint8').reshape((img.getRows(), img.getCols()))
c.stopCapture()
c.disconnect()
