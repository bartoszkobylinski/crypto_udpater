import subprocess
import random
import datetime
import pytz
import os

SIGNAL_GROUP_ID = os.getenv("SIGNAL_GROUP_ID")
SIGNAL_CLI_PATH = os.getenv("SIGNAL_CLI_PATH")


def send_signal_message(destination, message):
    command = [
        SIGNAL_CLI_PATH, 'send', '-g', destination, '-m', message
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"Failed to send message: {result.stderr.decode()}")
    else:
        print("Message sent successfully.")


def send_daily_message():
    with open('youtube_links.txt', 'r') as file:
        links = file.readlines()

    if links:
        random.shuffle(links)
        link_to_send = links.pop(0).strip()
        send_signal_message(SIGNAL_GROUP_ID, link_to_send)

        with open('youtube_links.txt', 'w') as file:
            file.writelines(links)

        with open('sent_links.txt', 'a') as file:
            file.write(link_to_send + '\n')
    else:
        print("No more links to send.")


def is_time_to_send():
    ny_tz = pytz.timezone('America/New_York')
    now = datetime.datetime.now(ny_tz)
    if now.hour in [11, 18]:
        send_daily_message()


is_time_to_send()
