# Names: Garrett Campbell, Bryan Yowler
# Assignment: Final Project ECE 4564
# File: business.py
# Tool that businesses will use in order to scan QR codes,
# send it to the government, and find out if QR code is valid
import cv2
import threading
from pyzbar import pyzbar
import winsound
import requests
import simpleaudio as sa
import tkinter as tk
from tkinter import *

green = (0, 255, 0)
red = (255, 0, 0)
announcement_read = True
num_admitted = 0
root = tk.Tk()
root.geometry("500x300")
var = IntVar()
var.set(num_admitted)
text_label = Label(root, text="Number of people permitted access today", relief=RAISED)
text_label.pack(side=TOP, expand=YES, fill=BOTH)
count_label = Label(root, textvariable=var, relief=RAISED, bd=4)
count_label.pack(side=TOP, expand=YES, fill=BOTH)


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
                t = threading.Thread(target=announce_result, args=(True, False), daemon=True)
                t.start()
            elif r.text == "Warning: Do not duplicate QR codes":  # if no vaccination found, show red and display no vaccination found message
                t = threading.Thread(target=announce_result, args=(False, True), daemon=True)
                t.start()
            else:
                t = threading.Thread(target=announce_result, args=(False, False), daemon=True)
                t.start()

        return True
    return False


def announce_result(vaccination_found, possible_duplication):
    global announcement_read
    global num_admitted
    announcement_read = False
    if vaccination_found:
        show_green()
        num_admitted += 1
        var.set(num_admitted)
        root.update_idletasks()
        filename = './business_audio/entry_permitted.wav'
        wave_obj = sa.WaveObject.from_wave_file(filename)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    elif possible_duplication:
        show_yellow()
        filename = './business_audio/duplicate_qr.wav'
        wave_obj = sa.WaveObject.from_wave_file(filename)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    else:
        show_red()
        filename = './business_audio/entry_denied.wav'
        wave_obj = sa.WaveObject.from_wave_file(filename)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    back_to_normal()
    announcement_read = True


def beep():
    winsound.Beep(700, 400)


def show_green():
    count_label.config(bg="#32CD32")


def show_red():
    count_label.config(bg="#ed1c24")


def show_yellow():
    count_label.config(bg="yellow")


def back_to_normal():
    count_label.config(bg="SystemButtonFace")


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
        if cv2.getWindowProperty('Barcode/QR code reader', cv2.WND_PROP_VISIBLE) < 1:
            break
    camera.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    thread = threading.Thread(target=main, daemon=True)
    thread.start()
    tk.mainloop()
