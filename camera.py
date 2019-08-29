import requests
import json
import urllib
import os
from datetime import datetime
import time
import os

import utils

FOLDER = "pics"
API_URL = 'http://10.0.0.1:10000/camera'


def take_picture():
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
        return

    response = json.loads(request.content)
    
    if 'result' not in response:
        print("Unable to take picture. Got response", response)
        return
        
    image_url = response['result'][0][0]
    filename = datetime.now().isoformat() + ".jpg"
    urllib.request.urlretrieve(image_url, os.path.join(FOLDER, filename))
    return filename

    
def update_table(filename, conn):
    sql = """
    INSERT INTO pictures (file, time)
    VALUES (%s, CURRENT_TIME())
    """
    conn.execute(sql, (filename))


def main():
    conn = utils.get_conn()
    print("Database connection established.")

    while True:        
        if utils.is_camera_on():
            filename = take_picture()
            update_table(filename, conn)
        else:
            print('Camera is off at', datetime.now())

        time.sleep(5)

        
if __name__ == '__main__':
    main()