import time
import random
import requests

# ====== OneM2M Configuration ======
CSE_IP = "dev-onem2m.iiit.ac.in"
CSE_PORT = 443
HTTPS = False
OM2M_ORIGIN = "Tue_20_12_22:Tue_20_12_22"
OM2M_MN = "/~/in-cse/in-name/"
OM2M_AE = "AE-WM/WM-WF"
OM2M_DATA_CONT = "WM-WF-PL00-70/Data"

# ====== ThingSpeak Configuration ======
THINGSPEAK_CHANNEL = "3004930"
THINGSPEAK_WRITE_API = "8PBJAK3JCNTB3NH7"

# ====== Telegram Bot Configuration ======
TELEGRAM_BOT_TOKEN = "8080932314:AAEss9FRi7hx-zBakJeyl06jb7caY2j9bIk"
TELEGRAM_CHAT_ID = "879323820"

# ====== Utility Functions ======

def get_epoch_time():
    return int(time.time())

def send_onem2m_data(timestamp, total_flow, flow_rate):
    data = f"[{timestamp}, {total_flow}, {flow_rate}]"
    protocol = "https" if HTTPS else "http"
    url = f"{protocol}://{CSE_IP}:{CSE_PORT}{OM2M_MN}{OM2M_AE}/{OM2M_DATA_CONT}"

    headers = {
        "X-M2M-Origin": OM2M_ORIGIN,
        "Content-Type": "application/json;ty=4"
    }

    payload = {
        "m2m:cin": {
            "con": data,
            "cnf": "text"
        }
    }

    print("\n Sending to oneM2M...")
    print("URL:", url)
    print("Payload:", payload)

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("oneM2M Response Code:", response.status_code)
    except Exception as e:
        print("Error posting to oneM2M:", e)
    finally:
        if 'response' in locals():
            response.close()

def send_thingspeak_data(timestamp, total_flow, flow_rate):
    url = "https://api.thingspeak.com/update"
    params = {
        "api_key": THINGSPEAK_WRITE_API,
        "field1": timestamp,
        "field2": total_flow,
        "field3": flow_rate
    }

    print("\n Sending to ThingSpeak...")
    print("URL:", url)
    print("Payload:", params)

    try:
        response = requests.get(url, params=params)
        print("ThingSpeak Response:", response.status_code, response.text)
    except Exception as e:
        print("Error posting to ThingSpeak:", e)
    finally:
        if 'response' in locals():
            response.close()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, data=payload)
        print("Telegram sent:", response.status_code)
    except Exception as e:
        print("Telegram Error:", e)
    finally:
        if 'response' in locals():
            response.close()
