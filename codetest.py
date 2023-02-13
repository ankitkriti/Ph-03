#################################USE This Code##############-#
import glob
import numpy as np
import cv2
import matplotlib.pyplot as plt
import os
import ipdb
from skimage import io as sio
from skimage.transform import resize
from skimage.feature import hog
from skimage.color import rgb2gray
# from train import detect
import subprocess
from imutils.contours import sort_contours
import joblib
import time
from urllib.request import urlopen
import sys
from pathlib import Path
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
from picamera import PiCamera
import json
import requests
import smtplib
import socket
import datetime
from time import sleep
import shutil
from collections import deque
import csv
import pdb
import config_WM
import psutil



error_log1 = []
str = "loaded libraries"
error_log1.append(str)



def access_csv(device_id, column):
    li = []
    with open ('configs.csv') as csvfile:
        content = csv.reader (csvfile)
        header = next (content)
        for row in content:
            if row[0] == device_id:
                myList = row

    head = header.index (column)
    try:
        return json.loads (myList[head])
    except:
        return myList[head]


# data = access_csv('Dummy', 'Ireading')

'''
1. URI-THe path in OM2M
2. Headers--auth key,data format inforamtion,
3. actual request--post you will get a response which is http response ---201=Success
'''


def create_data_cin(uri_cnt, value, cin_labels="", fmt_ex="json"):
    """
        Method description:
        Creates a data content instance(data_CIN) in the OneM2M framework/tree
        under the specified DATA CON
        Parameters:
        uri_cnt : [str] URI for the parent DATA CON
        fmt_ex : [str] payload format (json/XML)
    """

    headers = {
        'X-M2M-Origin': '{}:{}'.format (
            "devtest",
            "devtest"
        ),
        'Content-type': 'application/{};ty=4; charset=utf-8'.format (fmt_ex)
    }

    payload = {
        "m2m:cin": {
            "con": "{}".format (value),
            # "con": (
            #     json.dumps(value)
            #     if fmt_ex == 'json'
            #     else "{}".format(value)
            # ),
            "lbl": cin_labels,
            "cnf": "text"
        }
    }

    try:
        response = requests.post (uri_cnt, json=payload, headers=headers
                                  )
    except TypeError:
        response = requests.post (uri_cnt, data=json.dumps (payload),
                                  headers=headers)
    cin = None
    success = False
    if response.ok:
        cin = json.loads (response.content)['m2m:cin']['rn']
        success = True

    return success, response.status_code, cin


'''
all the present logic here

'''
relay_pin = 23
GPIO.setmode (GPIO.BCM)
GPIO.setup (relay_pin, GPIO.OUT)

WRITE_API = access_csv (config_WM.device_id, "write_api")  # config_WM.write_api		# Write API of Himalaya_parking
BASE_URL = "https://api.thingspeak.com/update?api_key={}".format (WRITE_API)
# Meter coordinates, starting from top-left in clockwise manner
pts_source = np.float32 (
    access_csv (config_WM.device_id, "pts_source"))  # [[391,311], [1747,319], [1750, 715], [389,685]])
width, height = 650, 215
pts_dst = np.float32 ([[0, 0], [width, 0], [width, height], [0, height]])
MIN_CONTOUR_AREA = 1500
RESIZED_IMAGE_WIDTH = 45
RESIZED_IMAGE_HEIGHT = 90
CROP_COORD = 540
memory_path = "/home"
count_internet = 0
node_dict = {"PH-03": "Pump House 3", "PH-02": "Pump House 2", "PR00-70": "Parijaat", "AD04-70": "Himalaya Rooftop 1",
             "AD04-71": "Himalaya Rooftop 2", "KB04-72": "Himalaya Rooftop 3", "KB04-73": "Himalaya Rooftop 4",
             "OBH00-70": "Palash Nivas 1", "OBH00-71": "Palash Nivas 2", "PH04-70": "Bakul Nivas 1",
             "PH04-71": "Bakul Nivas 2", "VN04-70": "Vindhya Rooftop 1", "VN04-71": "Vindhya Rooftop 2",
             "BB04-70": "Bodh Bhavan Rooftop 1", "BB04-71": "Bodh Bhavan Rooftop 2"}






def checkInternetSocket(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout (timeout)
        socket.socket (socket.AF_INET, socket.SOCK_STREAM).connect ((host, port))
        return True
    except socket.error as ex:
        print (ex)
        return False



def get_time():
    # Get time stamp
    ct = datetime.datetime.now()
    time_stamp = (str(ct.year) + '-' + str(ct.month) + '-' + str(ct.day) + ' ' + str(ct.hour) + ':' + str(ct.minute) + ':' + str(ct.second))
    print("time tamp = ")
    print(time_stamp)
    return time_stamp


def wait():
    # calculate the delay to the start of next minute
    next_minute = (datetime.datetime.now () + timedelta (seconds=25))
    delay = (next_minute - datetime.datetime.now ()).seconds
    time.sleep (delay)


def cam(save_path):
    camera = PiCamera ()
    camera.start_preview ()
    time.sleep (2)
    camera.capture (save_path)
    print ('Captured')


    error_log5 = []
    str = "cam captured"
    error_log5.append (str)


    camera.stop_preview ()
    camera.close ()


    error_log6 = []
    str = "cam closed"
    error_log6.append (str)


device_id = config_WM.device_id  # "PH-03"
time_stamp = get_time ()


def get_sorted_contour(img):
    img_gray = cv2.cvtColor (img, cv2.COLOR_BGR2GRAY)
    # img_gray = cv2.GaussianBlur(img_gray, (9, 9), 0)
    img_gray = cv2.medianBlur (img_gray, 15)
    thresh = cv2.adaptiveThreshold (img_gray, 255,
                                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV,
                                    33, 5)
    kernel = np.ones ((3, 3), np.uint8)
    thresh = cv2.dilate (thresh, kernel, iterations=5)
    thresh = cv2.erode (thresh, kernel, iterations=2)
    # plt.figure()
    # plt.imshow(thresh)
    # plt.title("Threshold Image")
    # plt.show()
    contours, hierachy = cv2.findContours (thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours, bbox = sort_contours (contours)
    contours = [contour for contour in contours if cv2.contourArea (contour) >= MIN_CONTOUR_AREA]
    for contour in contours:  # for each contour
        [intX, intY, intW, intH] = cv2.boundingRect (contour)  # get and break out bounding rect
        # draw rectangle around each contour
        cv2.rectangle (img,  # draw rectangle on original training image
                       (intX, intY),  # upper left corner
                       (intX + intW, intY + intH),  # lower right corner
                       (0, 0, 255),  # red
                       3)  # thickness
    # plt.figure()
    # plt.imshow(img)
    # plt.title("Detected Contours")
    # plt.show()
    return contours


def func(save_path, Filename):
    global cons
    img = sio.imread (save_path)
    # img = sio.imread("/home/pi/Desktop/images/img2021-08-05-22-52-56.jpg")
    # plt.imshow(img)
    # plt.show()
    matrix = cv2.getPerspectiveTransform (pts_source, pts_dst)
    img_meter = cv2.warpPerspective (img, matrix, (width, height))
    img_meter = img_meter[:, :CROP_COORD]
    # img_meter = img	# If you need to detect digits without coordinates, then comment above line and uncomment current line.
    # plt.imshow(img_meter)
    # plt.title("Extracted Meter")
    # plt.show()

    contours = get_sorted_contour (img_meter.copy ())

    error_log7 = []
    str = "contours made"
    error_log7.append (str)


    model = joblib.load ('rf_rasp_classifier.sav')  #

    error_log8 = []
    str = "model loaded"
    error_log8.append (str)



    result = ''
    for contour in contours:
        [intX, intY, intW, intH] = cv2.boundingRect (contour)
        imgROI = img_meter[intY:intY + intH, intX:intX + intW]

        img = cv2.cvtColor (imgROI, cv2.COLOR_BGR2GRAY)
        img = resize (img, (RESIZED_IMAGE_HEIGHT, RESIZED_IMAGE_WIDTH))
        flower = cv2.morphologyEx (img, cv2.MORPH_CLOSE, cv2.getStructuringElement (cv2.MORPH_ELLIPSE, (3, 3)))
        flower = cv2.morphologyEx (flower, cv2.MORPH_OPEN,
                                   cv2.getStructuringElement (cv2.MORPH_ELLIPSE, (11, 11)))

        img = cv2.erode (flower, cv2.getStructuringElement (cv2.MORPH_ELLIPSE, (3, 3)), iterations=3)
        img_feat = hog (img, orientations=9,
                        pixels_per_cell=(8, 8),
                        cells_per_block=(2, 2))
        digit_detected = model.predict (img_feat.reshape (1, -1))
        result += str (digit_detected[0])

    result = int (result) / 10
    stored_value.append (result)
    ans_gt = int (''.join (str (stored_value[-2]).split ('.')))
    ans = int (''.join (str (stored_value[-1]).split ('.')))
    min_cnt = 10
    print ("detected value:", result)

    imgtime1 = Filename[-1][8:-4]
    imgtime1 = datetime.strptime (imgtime1, '%m-%d-%H-%M-%S')

    imgtime2 = Filename[-2][8:-4]
    imgtime2 = datetime.strptime (imgtime2, '%m-%d-%H-%M-%S')

    time_diff = imgtime1 - imgtime2
    print (time_diff)
    time_diff = (time_diff.seconds) / 60
    print (int (time_diff))
    if (int (time_diff) < 1):
        time_diff = 1

    time = Filename[-1][3:-4]
    time = datetime.datetime.strptime (time, '%Y-%m-%d-%H-%M-%S')




    error_log9 = []
    str = "Before constraints (detection done)"
    error_log9.append (str)

######################### constraints ####################
    corr_val = 0

    for k in range (ans_gt, ans_gt + int (10 * time_diff), 1):

        ans_str = str (ans)
        k_str = str (k)

        while (len (ans_str) < 10):
            ans_str = "0" + ans_str
        while (len (k_str) < 10):
            k_str = "0" + k_str

        hamming_dist = 0
        for i in range (len (ans_str)):
            hamming_dist += (ans_str[i] != k_str[i])

        cnt = hamming_dist

        if (cnt < min_cnt):
            corr_val = k
            min_cnt = cnt

    stored_value[-1] = corr_val / 10

###########################################################

    error_log10 = []
    str = "after constraints "
    error_log10.append (str)



###################### Rate ###########################
    diff_val = stored_value[-1]-stored_value[-2]
    F1 = Filename[-1][8:-4]
    F2 = Filename[-2][8:-4]
    f1 = datetime.datetime.strptime (F1, '%m-%d-%H-%M-%S')
    f2 = datetime.datetime.strptime (F2, '%m-%d-%H-%M-%S')
    time_difference = (f1 - f2)
    p_sec = (time_difference.seconds) / 60

    rate_val = diff_val/p_sec
    rate_val = round(rate_val,2)
    f_rate.append (rate_val)
############################################################





###################### File creation ##############################


    # storing volume
    result_file = open (access_csv (config_WM.device_id, "vol_file"), 'a')
    result_file.writelines ([str (time) + ' ' + str (stored_value[-1]) + '\n'])
    result_file.close ()



    # storing rate
    result_file = open (access_csv (config_WM.device_id, "rate_file"), 'a')
    result_file.writelines ([str (time) + ' ' + str (f_rate[-1]) + '\n'])
    result_file.close ()



    # storing new values in variable.txt
    file_stored_value = str (round (stored_value[-1], 1))
    print ("Wrote on a file")
    f = open ('Variable.txt', 'w')
    f.write (file_stored_value)
    f.close ()

    error_log11 = []
    str = "before sending to gsheet "
    error_log11.append (str)

    # storing in google sheet
    try:
        requests.get ('https://script.google.com/macros/s/' + access_csv (config_WM.device_id,
                                                                          "gsheets") + '/exec?timestamp=%s&total_flow=%s&rate=%s&datval=%s' % (
                      str (Filename[-1][3:-4]), str (round (stored_value[-1], 1)), str (f_rate[-1]), str (result), str(error_log1[-1]), str(error_log2[-1]), str(error_log3[-1]), str(error_log4[-1]), str(error_log5[-1]), str(error_log6[-1]), str(error_log7[-1]), str(error_log8[-1]), str(error_log9[-1]), str(error_log10[-1]), str(error_log11[-1])   ))
        count_internet = 0
    except:
        print ("Not send to google sheets")
        count_check = checkInternetSocket ()

        error_log2 = []
        str = "Checked internet"
        error_log2.append (str)


        if count_check:
            count_internet += 1
        if count_internet > 7:
            os.system ("sudo systemctl restart codetest.service")

################################################################################

    # error_log11 = []
    # str = "file creation done "
    # error_log11.append (str)

def main():
    try:
        while True:
            # set LED high
            t1 = int (time.time ())
            Filename.append (str (datetime.datetime.now ().strftime ("img%Y-%m-%d-%H-%M-%S") + ".jpg"))
            print ("start")
            subprocess.call (
                "/home/pi/Desktop/waterspcrc/" + access_csv (config_WM.device_id, "fileD") + "/run_cmd_bash.sh")
            os.system ("sudo /etc/init.d/ntp stop")
            try:
                os.system ("sudo ntpdate " + access_csv (config_WM.device_id, 'time'))
            except:
                pass
            os.system ("sudo /etc/init.d/ntp start")
            print ("end")
            print ("Setting high - LED ON")
            GPIO.output (relay_pin, GPIO.HIGH)
            save_path = '/home/pi/Desktop/images/' + str (Filename[-1])

            error_log3 = []
            str = "Before cam func"
            error_log3.append (str)


            cam (save_path)

            error_log4 = []
            str = "after cam func"
            error_log4.append (str)


            time.sleep (3)
            # set LED low
            print ("Setting low - LED OFF")
            GPIO.output (relay_pin, GPIO.LOW)


            daterec = []
            func (save_path, Filename)
            print ("after gsheets")
            path = '/'
            use_percent = psutil.disk_usage (path).percent




            hello = requests.get (
                "https://script.google.com/macros/s/AKfycbwRYxc69FWSf_qaZVlNx7ACr5UkRysUmzN_24v91yj0jgAVxR2KfGlX7XW1But5d6a7/exec")
            new_ar = hello.content.decode ("utf-8").strip ('][').split (',')
            for i in range (len (new_ar)):
                new_ar[i] = float (new_ar[i])
            print (new_ar)
            new_val = new_ar[int (access_csv (config_WM.device_id, "sno")) - 1]
            var = open ('var2.txt', 'r')
            read_var = float (var.read ())
            var.close ()
            if read_var == new_val:
                print ("ok")
            else:
                write_val = open ("var2.txt", "w")
                write_val.write (str (new_val))
                write_val.close ()
                write_val2 = open ("Variable.txt", "w")
                write_val2.write (str (new_val))
                write_val2.close ()
                print ("changed.......")
                os.system ("sudo systemctl restart codetest.service")

            if str (access_csv (config_WM.device_id, "send_img")) == "1":
                if (datetime.datetime.now ().minute <= 30):
                    try:
                        _TOKEN = "bot2007916477:AAGHVLP0tOgV4oTw2_CRXB7AmXuVLwLkuck"
                        data = {"chat_id": "@IIIT_Bot_WM_RF",
                                "caption": str (node_dict[str (config_WM.device_id)]) + str (" (Mem Usg: ") + str (
                                    use_percent) + str (")")}
                        url = "https://api.telegram.org/%s/sendPhoto" % _TOKEN
                        image_path = save_path

                        new_image = cv2.imread (image_path)
                        new_image = cv2.resize (new_image, (150, 84))
                        new_path = "/home/pi/Desktop/test_send.jpg"
                        cv2.imwrite (new_path, new_image)

                        with open (new_path, "rb") as image_file:
                            ret = requests.post (url, data=data, files={"photo": image_file}, timeout=10)
                            print (ret)
                        os.remove (new_path)


                    except:
                        pass

            t2 = int (time.time ())
            # wait()
            delay = 600 - (t2 - t1)
            if delay <= 0:
                delay = 0.5
            print (delay)

            if use_percent > 80:
                # if f_rate[-1] == 0:
                os.remove (save_path)

            # if (datetime.datetime.now ().minute % 5 != 0):
            #     try:
            #         os.remove (save_path)
            #     except:
            #         pass

            time.sleep (delay)
    except KeyboardInterrupt:
        GPIO.cleanup ()
    finally:
        print ("executed successfully")
        os.system ("sudo systemctl restart codetest.service")


if __name__ == '__main__':
    stored_value = deque (5 * [0], 5)  # creating list
    cons = 0
    f_rate = deque (5 * [0], 5)
    Filename = deque (5 * [0], 5)
    print ("read")
    f = open ('Variable.txt', 'r')
    reading_file = f.read ()
    f.close ()
    reading_file = float (reading_file)
    stored_value.append (reading_file)  # 33875.3
    Filename.append (str (datetime.datetime.now ().strftime ("img%Y-%m-%d-%H-%M-%S") + ".jpg"))
    time.sleep (1)
    main ()






