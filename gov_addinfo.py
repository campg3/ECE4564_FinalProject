# Names: Garrett Campbell, Bryan Yowler
# Assignment: Final Project ECE 4564
# File: gov_addinfo.py
# Purpose: Independent Python program used to insert vaccination information
#          into MongoDB database.

import tkinter as tk
from pymongo import MongoClient
import gov_keys
from cryptography.fernet import Fernet
from datetime import date
import pickle
import base64
import hashlib

# Initialize tk and variables
root = tk.Tk()
root.geometry("600x400")
firstname_var = tk.StringVar()
middlename_var = tk.StringVar()
lastname_var = tk.StringVar()
ssn_var = tk.StringVar()
dob_var = tk.StringVar()

# Connect to MongoDB Database
client = MongoClient(
        "mongodb+srv://" + gov_keys.DATABASE_ADMIN_USERNAME + ":" + gov_keys.DATABASE_ADMIN_PASSWORD +
        "@cluster0.mm83g.mongodb.net/" +
        gov_keys.DATABASE_NAME + "?retryWrites=true&w=majority")
db = client[gov_keys.DATABASE_NAME]
collection = db[gov_keys.PATIENT_COLLECTION]
development_collection = db[gov_keys.DEVELOPMENT_COLLECTION]

def submit():
        # Get all fields from GUI
        firstname = firstname_var.get()
        middlename = middlename_var.get()
        lastname = lastname_var.get()
        ssn = ssn_var.get()
        dob = dob_var.get()

        # Create data for QR code and encrypt
        num_business_requests = 0
        num_individual_requests = 0
        qr_data = str(firstname + "_" + middlename + "_" + lastname + "_" + ssn[-4:])
        encryption_key = str(firstname + "_" + lastname + "_" + ssn[-4:] + "_" + dob)
        hash_var = hashlib.md5(encryption_key.encode())
        gen_key = base64.urlsafe_b64encode(hash_var.hexdigest().encode())
        key = Fernet(gen_key)
        encrypted_qr = key.encrypt(qr_data.encode())

        # Add encryption entry to database
        today = date.today()
        current_date = today.strftime("%m/%d/%Y")
        vaccine_entry = {"FirstName": key.encrypt(firstname.encode()).decode(), "MiddleName": key.encrypt(middlename.encode()).decode(), "LastName": key.encrypt(lastname.encode()).decode(),
                         "SSN": key.encrypt(ssn.encode()).decode(), "DateOfBirth": key.encrypt(dob.encode()).decode(), "QRCodeData": encrypted_qr.decode(), "DateVaccinated": key.encrypt(current_date.encode()).decode(),
                         "NumBusinessRequests": num_business_requests, "NumIndividualRequests": num_individual_requests}
        develop_entry = {"FirstName": firstname,
                         "MiddleName": middlename,
                         "LastName": lastname,
                         "SSN": ssn, "DateOfBirth": dob,
                         "QRCodeData": qr_data,
                         "DateVaccinated": current_date}
        x = collection.insert_one(vaccine_entry)
        dev = development_collection.insert_one(develop_entry)

        # Reset variables for next user to input
        firstname_var.set("")
        middlename_var.set("")
        lastname_var.set("")
        ssn_var.set("")
        dob_var.set("")

# Create labels and entry boxes for all fields
firstname_label = tk.Label(root, text='First Name', font=('calibre', 12, 'bold'))
firstname_entry = tk.Entry(root, textvariable=firstname_var, font=('calibre', 12, 'normal'))
middlename_label = tk.Label(root, text='Middle Name', font=('calibre', 12, 'bold'))
middlename_entry = tk.Entry(root, textvariable=middlename_var, font=('calibre', 12, 'normal'))
lastname_label = tk.Label(root, text='Last Name', font=('calibre', 12, 'bold'))
lastname_entry = tk.Entry(root, textvariable=lastname_var, font=('calibre', 12, 'normal'))
ssn_label = tk.Label(root, text='Social Security Number (XXXXXXXXX)', font=('calibre', 12, 'bold'))
ssn_entry = tk.Entry(root, textvariable=ssn_var, font=('calibre', 12, 'normal'))
dob_label = tk.Label(root, text='Date of Birth (MM/DD/YYYY)', font=('calibre', 12, 'bold'))
dob_entry = tk.Entry(root, textvariable=dob_var, font=('calibre', 12, 'normal'))
submit_btn = tk.Button(root, text='Submit', command=submit)

# Place entries and button in grid
firstname_label.grid(row=0, column=0)
firstname_entry.grid(row=0, column=1)
middlename_label.grid(row=1, column=0)
middlename_entry.grid(row=1, column=1)
lastname_label.grid(row=2, column=0)
lastname_entry.grid(row=2, column=1)
ssn_label.grid(row=3, column=0)
ssn_entry.grid(row=3, column=1)
dob_label.grid(row=4, column=0)
dob_entry.grid(row=4, column=1)
submit_btn.grid(row=5, column=1)

# Start GUI main loop
tk.mainloop()
