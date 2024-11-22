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
BASE_URL = "http://127.0.0.1:8000"

PAYING_PREDICT_URL = BASE_URL + "/paying-predict"
FREE_PREDICT_URL = BASE_URL + "/free-predict"
TRAIN_PREDICT_URL = BASE_URL + "/train"

post_details = {'title': 'testtt', 'body': 'test bodyy'}

# sending get request and saving the response as response object

def paying_predict(i):
    with open('example_img.png', 'rb') as file:
        files = {'file': file}
        r = requests.post(url = PAYING_PREDICT_URL, files=files)
    print(i, ": ", r)

def free_predict(i):
    with open('example_img.png', 'rb') as file:
        files = {'file': file}
        r = requests.post(url = FREE_PREDICT_URL, files=files)
    print(i, ": ", r)

def train(i):

    with open("borzoi.png", 'rb') as borzoi, open("impala.png", 'rb') as impala, open("komondor.png", 'rb') as komondor, open("meerkat.png", 'rb') as meerkat, open("vizsla.png", 'rb') as vizsla, open("wallaby.png", 'rb') as wallaby:
        
        files = [('files', ('borzoi.jpg', borzoi, 'image/jpeg')),
        ('files', ('impala.jpg', impala, 'image/jpeg')),
        ('files', ('komondor.jpg', komondor, 'image/jpeg')),
        ('files', ('meerkat.jpg', meerkat, 'image/jpeg')),
        ('files', ('vizsla.jpg', vizsla, 'image/jpeg')),
        ('files', ('wallaby.jpg', wallaby, 'image/jpeg')),]

        data = { 'labels': ['borzoi', 'impala', 'Komondor', 'meerkat', 'Vizsla', 'wallaby'] }

        r = requests.post(url = TRAIN_PREDICT_URL, files=files, data=data)
    
    print(i, ": ", r)


free_predict(1)
paying_predict(2)
train(3)

# track number of outstanding requests
# could even do explicit admissions control from here
# live_threads = []

# for i in range(NUM_REPS):

#     rand_perc = random.uniform(0, 100)

#     if rand_perc < PERCENT_STATIC:
#         t1 = threading.Thread(target=paying_predict, args=(i,))
#     elif rand_perc < PERCENT_STATIC + PERCENT_DYNAMIC:
#         t1 = threading.Thread(target=free_predict, args=(i,))
#     elif rand_perc < PERCENT_STATIC + PERCENT_DYNAMIC + PERCENT_FG:
#         t1 = threading.Thread(target=paying_predict, args=(i,))
#     else:
#         t1 = threading.Thread(target=paying_predict, args=(i,))
    
#     live_threads.append(t1)
#     t1.start()

#     while len(live_threads) > NUM_REQS_LIVE:
#         for t in live_threads:
#             if not t.is_alive():
#                 live_threads.remove(t)
