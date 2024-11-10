# importing the requests library
import requests
import os
import random
from time import sleep
import threading


# affinity_mask = {1} 
# pid = 0
# os.sched_setaffinity(0, affinity_mask) 



NUM_REPS = 1000

NUM_REQS_LIVE = 50


PERCENT_STATIC = 60
PERCENT_DYNAMIC = 33
PERCENT_FG = 6
PERCENT_BG = 1

# api-endpoint
BASE_URL = "http://localhost:5000"

GET_ONE_URL = BASE_URL + "/36"
GET_ALL_URL = BASE_URL
CREATE_URL = BASE_URL + "/create"
UPLOAD_URL = BASE_URL + "/docount"


post_details = {'title': 'testtt', 'body': 'test bodyy'}
file_to_count = {'file': open('10mb.txt' ,'rb')}

# sending get request and saving the response as response object

def get_one(i):
    r = requests.get(url = GET_ONE_URL)
    print(i, ": ", r)

def get_all(i):
    r = requests.get(url = GET_ALL_URL)
    print(i, ": ", r)

def create(i):
    r = requests.post(url = CREATE_URL, data=post_details)
    print(i, ": ", r)

def upload(i):
    r = requests.post(url = UPLOAD_URL, files=file_to_count)
    print(i, ": ", r)


# track number of outstanding requests
live_threads = []

for i in range(NUM_REPS):

    rand_perc = random.uniform(0, 100)

    if rand_perc < PERCENT_STATIC:
        t1 = threading.Thread(target=get_one, args=(i,))
    elif rand_perc < PERCENT_STATIC + PERCENT_DYNAMIC:
        t1 = threading.Thread(target=get_all, args=(i,))
    elif rand_perc < PERCENT_STATIC + PERCENT_DYNAMIC + PERCENT_FG:
        t1 = threading.Thread(target=create, args=(i,))
    else:
        t1 = threading.Thread(target=upload, args=(i,))
    
    live_threads.append(t1)
    t1.start()

    while len(live_threads) > NUM_REQS_LIVE:
        for t in live_threads:
            if not t.is_alive():
                live_threads.remove(t)

sleep(1)