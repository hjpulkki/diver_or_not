"""Custom timelapse for Sony RX100 M2"""
import json
import os
from datetime import datetime
import time
import urllib

import requests

import utils

FOLDER = "pics"
API_URL = 'http://10.0.0.1:10000/camera'


def take_picture():
    """Takes a picture and stores it to the pics folder"""
    json_request = {
        "method": "actTakePicture",
        "params": [],
        "id": 1,
        "version": "1.0"
    }
    try:
        request = requests.post(API_URL, json.dumps(json_request))
    except requests.exceptions.ConnectionError:
        print("Failed to connect to camera.")
        return None

    response = json.loads(request.content)

    if 'result' not in response:
        print("Unable to take picture. Got response", response)
        return None

    image_url = response['result'][0][0]
    filename = datetime.now().isoformat() + ".jpg"
    urllib.request.urlretrieve(image_url, os.path.join(FOLDER, filename))
    return filename


def update_table(filename, conn):
    """Add new picture to the database. This will trigger automatic evaluation."""
    sql = """
    INSERT INTO pictures (file, time)
    VALUES (%s, CURRENT_TIME())
    """
    conn.execute(sql, (filename))


def main():
    """Timelapse: Takes pictures adds them to the database."""
    conn = utils.get_conn()
    print("Database connection established.")

    while True:
        if utils.is_camera_on():
            filename = take_picture()
            update_table(filename, conn)
        else:
            print('Camera is off at', datetime.now())

        time.sleep(3)


if __name__ == '__main__':
    main()
