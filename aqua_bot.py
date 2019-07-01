import datetime  # Importing the datetime library
import telepot   # Importing the telepot library
from telepot.loop import MessageLoop    # Library function to communicate with telegram bot
from time import sleep      # Importing the time library to provide the delays in program
import os
import utils
import subprocess

import config

conn = utils.get_conn()
authorized_users = [
    35833581,   # Heikki
]

previous_pictures = {}
picture_generators = {}


def get_best(time, trained_model='score_model_2.p'):
    sql = '''
    SELECT file, prediction
    FROM predictions
    WHERE
        file > DATE_SUB(curdate(), INTERVAL %s HOUR)
        AND trained_model = %s
    ORDER BY prediction DESC
    LIMIT 1000
    '''
    all_results = conn.execute(sql, (time, trained_model)).fetchall()
    print("found", len(all_results), "results")
    for res in all_results:
        description = "Picture {}. Rate it from 0 to 10".format(res[0], res[1])
        yield res[0], description


def get_random(time):
    sql = '''
    SELECT file, prediction
    FROM predictions
    WHERE
        file > DATE_SUB(curdate(), INTERVAL %s HOUR)
        AND prediction > 0.06  /* Filter out the worst images */
    LIMIT 1000
    '''
    all_results = conn.execute(sql, (time,)).fetchall()

    for res in all_results:
        description = "Picture {}. Rate it from 0 to 10".format(res[0], res[1])
        yield res[0], description

def send_next(user, chat_id):
    try:
        filename, description = next(picture_generators[user])
        filepath = 'pics/{}'.format(filename)
        print("Opening file", filepath)
        previous_pictures[user] = filename
        bot.sendPhoto(chat_id=chat_id, photo=open(filepath, 'rb'))
        # bot.sendMessage(chat_id, description)
    except StopIteration:
        bot.sendMessage(chat_id, 'No more pictures in query')


def get_time(params, default=24):
    time = default
    if len(params) > 0:
        try:
            time = int(params[0])
        except ValueError:
            time = default
    time = min(time, 100000)   # Too large value messes up the filter by string inequality
    print("time", time)
    return time


def handle(msg):
    chat_id = msg['chat']['id'] # Receiving the message from telegram
    command = msg['text']   # Getting text from the message
    user = msg['from']['id']
    authorized = user in authorized_users

    print(msg)
    temp = msg['text'].split(" ")
    command = temp[0]
    params = temp[1:]

    print ('Received:')
    print(command)

    # Comparing the incoming message to send a reply according to it
    if command == '/time':
        bot.sendMessage(chat_id, str("Time: ") + str(now.hour) + str(":") + str(now.minute) + str(":") + str(now.second))
    elif command == '/pic':
        pictures = os.listdir('pics')
        latest_pic = sorted(pictures)[-1]
        bot.sendPhoto(chat_id=chat_id, photo=open('pics/{}'.format(latest_pic), 'rb'))
    elif command == '/best':
        bot.sendMessage(chat_id, 'Starting to send pictures. Reply with a number between 0 and 10 to rate them.')
        time = get_time(params)
        picture_generators[user] = get_best(time)
        send_next(user, chat_id)
    elif command == '/random':
        bot.sendMessage(chat_id, 'Starting to send pictures. Reply with a number between 0 and 10 to rate them.')
        time = get_time(params)
        picture_generators[user] = get_random(time)
        send_next(user, chat_id)
    elif command == '/halt':
        if not authorized:
            bot.sendMessage(chat_id, 'You are not authorized to use this command. Contact @Heikki for access')
            return
        os.system('sudo halt -p')
    elif command == '/os':
        if not authorized:
            bot.sendMessage(chat_id, 'You are not authorized to use this command. Contact @Heikki for access')
            return
        result = subprocess.check_output(params)
        bot.sendMessage(chat_id, result)
    elif command == '/camera':    # Commands to turn camera on/off.
        if not authorized:
            bot.sendMessage(chat_id, 'You are not authorized to use this command. Contact @Heikki for access')
            return

        if len(params) < 1:
            bot.sendMessage(chat_id, 'Unknown parameter for command camera. Possible values are on, off, status')

        if params[0] == 'off':
            utils.set_camera(False)
            bot.sendMessage(chat_id, 'Camera is now turned off.')
        elif params[0] == 'on':
            utils.set_camera(True)
            bot.sendMessage(chat_id, 'Camera is now turned on.')
        elif params[0] == 'status':
            status = utils.is_camera_on()
            bot.sendMessage(chat_id, 'Camera status is {}'.format(status))
        else:
            bot.sendMessage(chat_id, 'Unknown parameter for command camera. Possible values are on, off, status')
    else:
        try:
            rating = int(command)

            sql = """
            INSERT INTO scores (file, score, user, time) 
            VALUES (%s, %s, %s, CURRENT_TIME())
            """
            conn.execute(sql, (previous_pictures[user], rating, user))

            send_next(user, chat_id)
        except ValueError:
            bot.sendMessage(chat_id, "Unknown command")

def run_bot():
    global bot
    bot = telepot.Bot(config.tg_token)
    print (bot.getMe())
    MessageLoop(bot, handle).run_as_thread()
    while True:
        sleep(1)

if __name__ == '__main__':
    while True:
        try:
            bot = telepot.Bot(config.tg_token)
            run_bot()
        except:
            print("AquaBot crashed.")
            sleep(30)
            print("Reconnecting")
