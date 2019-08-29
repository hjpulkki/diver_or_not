import pandas as pd
import os
import sqlalchemy
import cv2
import matplotlib.pyplot as plt

import config


img_folder = 'pics/'
score_folder = 'score_data/'
database = 'dc'
status_file = 'camera_status.txt'


def get_conn():
    db_url = sqlalchemy.engine.url.URL('mysql', username=config.username, password=config.password, host='localhost', database=database)
    conn = sqlalchemy.create_engine(db_url)
    conn.connect()
    return conn


def get_scores():
	dfs = []
	for filename in os.listdir(score_folder):
		dfs.append(pd.read_csv(score_folder + filename, header=None))
	df = pd.concat(dfs, axis=0)
	df.columns = ['file', 'score']
	mask = (df.score >= 0) & (df.score <= 10)
	return df[mask]

def show_image(filename):
    print("/files/diver_or_not/{}{}".format(img_folder, filename))
    if not os.path.isfile(img_folder + filename):
        return
    im = cv2.imread(img_folder + filename)
    plt.imshow(im)
    plt.show()


def is_camera_on():
    with open(status_file, 'r') as f:
        return f.readline().strip().lower() == 'on'

def set_camera(status):
    status_string = 'off'
    if status:
        status_string = 'on'
    with open(status_file, 'w') as f:
        f.write(status_string)
 
