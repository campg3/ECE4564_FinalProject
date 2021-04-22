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
import beepy

green = (0, 255, 0)
red = (255, 0, 0)


def read_barcodes(frame):
    barcodes = pyzbar.decode(frame)
    if len(barcodes) == 1:
        for barcode in barcodes:
            x, y, w, h = barcode.rect
            barcode_info = barcode.data.decode('utf-8')

            # send data to government business endpoint, test
            # if vaccination confirmed, show green and display confirmed message
            # if no vaccination found, show red and display no vaccination found message
            t2 = threading.Thread(target=beep, daemon=True)
            t2.start()
            cv2.rectangle(frame, (x, y), (x + w, y + h), green, 2)
        return True
    return False


def beep():
    winsound.Beep(700, 400)


def delay():
    time.sleep(3)


def main():
    t1 = threading.Thread(target=delay, daemon=True)
    camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    while ret:
        ret, frame = camera.read()
        if not t1.is_alive():
            if read_barcodes(frame):
                t1 = threading.Thread(target=delay, daemon=True)
                t1.start()
        cv2.imshow('Barcode/QR code reader', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    camera.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
