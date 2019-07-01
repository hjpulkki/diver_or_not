# coding: utf-8

# # Steps
# - Process all unprocessed pictures (this notebook, also a cronjob)
# - Train model (done only once with notebook)
# - Run predictions for all unprocessed files (notebook 3, also cronjob)
# - Get predictions from database (telegram bot)

import utils
import cv2
import matplotlib.pyplot as plt
import time
import pandas as pd
from sklearn import linear_model
from sklearn.model_selection import train_test_split
import datetime
import os

import numpy as np
import pickle

from keras.preprocessing import image
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array

from keras.applications import MobileNet
from keras.applications.mobilenet import preprocess_input
from keras.applications.mobilenet import decode_predictions

representation_model = 'mobilenet_2'
trained_model = 'score_model_2.p'

model = MobileNet(weights='imagenet')
model.layers.pop()  # Remove last layer

model_2 = pickle.load(open("models/{}".format(trained_model), "rb" ))
features = np.arange(1,1001)   # mobilenet_2

def get_features(filename):
    image = load_img(filename, target_size=(224, 224))
    image = img_to_array(image)
    image = image.reshape((1, image.shape[0], image.shape[1], image.shape[2]))
    image = preprocess_input(image)
    return model.predict(image).ravel() 


def get_unprocessed_files(conn):
    # Not needed any more since camera script updates the table directly.
    # pictures = os.listdir('pics')
    # pics = pd.DataFrame(pictures, columns=['file'])
    # pics.to_sql('pictures', conn, if_exists='replace')  # Update pictures table with overwrite.

    sql = """
    SELECT a.file
    FROM (SELECT DISTINCT file FROM pictures) a
    LEFT JOIN (SELECT DISTINCT file FROM processed) b
        ON a.file = b.file
    WHERE b.file IS NULL
    """
    return pd.read_sql(sql, conn)

def process_batch(conn):
    unprocessed_files = get_unprocessed_files(conn)
    print("Found {} unprocessed files.".format(unprocessed_files.index.size))
    if unprocessed_files.index.size > 100:
        print("Processing first 100")
        unprocessed_files = unprocessed_files.head(100)

    unprocessed_files['time'] = datetime.datetime.now().isoformat()
    unprocessed_files['model'] = representation_model

    # Create dataframe for predictions
    predictions = pd.DataFrame()
    predictions['file'] = unprocessed_files['file']
    predictions['representation_model'] = representation_model
    predictions['prediction'] = None
    predictions['trained_model'] = trained_model

    for ind, row in unprocessed_files.iterrows():
        filename = row['file']
        try:
            representation = get_features(utils.img_folder + filename)
            with open("data/{}/{}.csv".format(representation_model, filename), "w" ) as f:
                f.write(filename + "," + ",".join([str(a) for a in representation]) + "\n")

            predictions.loc[ind, 'prediction'] = model_2.predict_proba(
                representation.reshape(1, -1)
            )[0,1]

        except Exception as e:
            print('error processing file', filename)
            print(e)

    unprocessed_files.to_sql('processed', conn, if_exists='append')
    predictions.to_sql('predictions', conn, if_exists='append')

if __name__ == '__main__':
    conn = utils.get_conn()
    while True:
        process_batch(conn)
        time.sleep(3)
