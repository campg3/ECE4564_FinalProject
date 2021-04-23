# Names: Garrett Campbell, Bryan Yowler
# Assignment: Final Project ECE 4564
# File: business.py
# Tool that businesses will use in order to scan QR codes,
# send it to the government, and find out if QR code is valid
import cv2
import time
import threading
from pyzbar import pyzbar
import winsound
import requests
import simpleaudio as sa

green = (0, 255, 0)
red = (255, 0, 0)
announcement_read = True


def read_barcodes(frame):
    barcodes = pyzbar.decode(frame)
    if len(barcodes) == 1:
        for barcode in barcodes:
            t2 = threading.Thread(target=beep, daemon=True)
            t2.start()
            x, y, w, h = barcode.rect
            barcode_info = barcode.data.decode('utf-8')

            # send data to government business endpoint, test
            r = requests.get('http://66.199.73.35:3001/business', auth=("admin", "secret"), params={'qr': barcode_info})

            # if vaccination confirmed, show green and display confirmed message
            if r.text == "Vaccination Record Found":
                t = threading.Thread(target=announce_result, args=(True,), daemon=True)
                t.start()
            else:  # if no vaccination found, show red and display no vaccination found message
                t = threading.Thread(target=announce_result, args=(False,), daemon=True)
                t.start()

        return True
    return False


def announce_result(vaccination_found):
    global announcement_read
    announcement_read = False
    if vaccination_found:
        filename = './business_audio/entry_permitted.wav'
        wave_obj = sa.WaveObject.from_wave_file(filename)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    else:
        filename = './business_audio/entry_denied.wav'
        wave_obj = sa.WaveObject.from_wave_file(filename)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    announcement_read = True


def beep():
    winsound.Beep(700, 400)


def main():
    global announcement_read
    camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    while ret:
        ret, frame = camera.read()
        if announcement_read:
            read_barcodes(frame)
        cv2.imshow('Barcode/QR code reader', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    camera.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
