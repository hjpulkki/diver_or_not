from picamera import PiCamera
from time import sleep
import cv2
from datetime import datetime
import keyboard
import numpy as np

from Adafruit_BNO055 import BNO055
import utils

folder = "pics/"


def iso_datestring():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")


def take_picture():
    heading, roll, pitch = bno.read_euler()
    sys, gyro, accel, mag = bno.get_calibration_status()
    print('Heading={0:0.2F} Roll={1:0.2F} Pitch={2:0.2F}\tSys_cal={3} Gyro_cal={4} Accel_cal={5} Mag_cal={6}'.format(
        heading, roll, pitch, sys, gyro, accel, mag))


    filename = iso_datestring() + ".jpg"
    print("Pic", filename)
    camera.capture(folder + filename)

    sql = """
    INSERT INTO pictures (file, heading, roll, pitch, sys_cal, gyro_cal, accel_cal, mag_cal, time)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIME())
    """
    conn.execute(sql, (filename, heading, roll, pitch, sys, gyro, accel, mag))


if __name__ == '__main__':
    camera = PiCamera()
    camera.start_preview()
    print("Camera running")

    for i in range(10):
        try:
            bno = BNO055.BNO055(serial_port='/dev/ttyUSB0')
            if not bno.begin():
                print('Failed to initialize BNO055! Is the sensor connected?')

            status, self_test, error = bno.get_system_status()
            print('Rotation sensor status: {0}'.format(status))
        except:
            print("Failed to initialize rotation sensor. Retrying 10 times.")
        break

    conn = utils.get_conn()
    print("Database connection established.")

    while True:
        # camera.stop_preview()
        # cv2.imshow('black screen', np.array([[0]]))
        
        if utils.is_camera_on():
            take_picture()
        else:
            print('Camera is off at', iso_datestring())


        if keyboard.is_pressed('q'):
            break
        sleep(5)

    camera.stop_preview()
