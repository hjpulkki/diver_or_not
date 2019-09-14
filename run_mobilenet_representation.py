# coding: utf-8
"""Automatic evaluation of picture quality.
Steps
- Process all unprocessed pictures (this notebook, also a cronjob)
- Train model (done only once with notebook)
- Run predictions for all unprocessed files (notebook 3, also cronjob)
- Get predictions from database (telegram bot)
"""

import time
import datetime
import pickle

import numpy as np
import pandas as pd
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from keras.applications import MobileNet
from keras.applications.mobilenet import preprocess_input

import utils

representation_model = 'mobilenet_2'
trained_models = ['score_model_2.p', 'score_model_3.p']

model = MobileNet(weights='imagenet')
model.layers.pop()  # Remove last layer

features = np.arange(1, 1001)   # mobilenet_2


def get_model(model_filename):
    with open("models/{}".format(model_filename), "rb") as file:
        return pickle.load(file)


model_2_dict = {
    trained_model: get_model(trained_model)
    for trained_model in trained_models
}


def get_features(filename):
    image = load_img(filename, target_size=(224, 224))
    image = img_to_array(image)
    image = image.reshape((1, image.shape[0], image.shape[1], image.shape[2]))
    image = preprocess_input(image)
    return model.predict(image).ravel()


def get_unprocessed_files(conn):
    sql = """
        SELECT DISTINCT file
        FROM pictures
        WHERE file > (SELECT MAX(file) FROM processed)
        ORDER BY file
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

    predictions_dict = {}

    for trained_model in trained_models:
        predictions = predictions.copy()
        predictions['trained_model'] = trained_model
        predictions_dict[trained_model] = predictions

    for ind, row in unprocessed_files.iterrows():
        filename = row['file']
        try:
            representation = get_features(utils.img_folder + filename)
            with open("data/{}/{}.csv".format(representation_model, filename), "w") as f:
                f.write(filename + "," + ",".join([str(a) for a in representation]) + "\n")

            for trained_model in trained_models:
                if trained_model == 'score_model_2.p':
                    # Classification models
                    pred = model_2_dict[trained_model].predict_proba(
                        representation.reshape(1, -1)
                    )[0, 1]
                else:
                    # Regression models
                    pred = model_2_dict[trained_model].predict(representation.reshape(1, -1))

                predictions_dict[trained_model].loc[ind, 'prediction'] = pred

        except Exception as e:
            print('error processing file', filename)
            print(e)

    unprocessed_files.to_sql('processed', conn, if_exists='append')

    for trained_model in trained_models:
        predictions_dict[trained_model].to_sql('predictions', conn, if_exists='append')

def main():
    conn = utils.get_conn()
    while True:
        process_batch(conn)
        time.sleep(3)


if __name__ == '__main__':
    main()
