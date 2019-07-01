This project contains code which is meant to be used in an underwater Raspberry Pi "diving computer". Three main parts are:

1. Camera. Takes a picture every 5 seconds with the Rpi default camera, and stores it in pics/ folder. This script also uses a BNO055 sensor to get the current euler heading. This value is stored in the database for later use.
2. Machine learning module which processes the images. It automatically predicts which images are good or bad, and stores these results to the database.
3. A telegram bot. Can be used to turn the camera on or off, control the device, or view best pictures with a mobile phone.

Most of this code has been written in a tent or in a car with a rpi monitor, so the quality is not always the best possible :)

The initial goal of this project was to detect automatically whether there is a diver in the image or not.
