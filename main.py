import time

from m5ui import M5Img
from m5stack import lcd
import network
import urequests as requests

from config import WIFI_SSID, WIFI_PASSWORD, SERVER_URL, SERVER_TOKEN


sta_if = network.WLAN(network.STA_IF)
if not sta_if.active():
    sta_if.active(True)

if not sta_if.isconnected():
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)

while not sta_if.isconnected():
    print('Connecting to network...')

print(sta_if.ifconfig())

width, height = lcd.screensize()

print('width, height', width, height)

CHUNK = 32 * 1024

img = None
while True:
    try:
        response = requests.get(SERVER_URL, headers={'Authorization': 'Bearer ' + SERVER_TOKEN})
    except Exception as e:
        print('Unable to download image', e)
        continue

    print('Image download', response.status_code)
    if response.status_code >= 400:
        print('Unable to download image', response.status_code)
        response.close()
        continue

    try:
        with open('current.png', 'wb') as f:
            while True:
                data = response.raw.read(CHUNK)
                f.write(data)
                if len(data) < CHUNK:
                    break
    except Exception as e:
        print('Unable to download and save image', e)
        response.close()
        continue

    response.close()

    print('Image written')

    # lcd.clear()
    print('Image show')
    if not img:
        img = M5Img(0, 0, 'current.png', True)
    else:
        img.changeImg('current.png')


    print('LCD show')
    lcd.show()

    print('Sleeping...')
    time.sleep(10)
    print('Done sleeping')
