# Names: Garrett Campbell, Bryan Yowler
# Assignment: Final Project ECE 4564
# File: gov_server.py
# Purpose: Flask server used as the government website that users and businesses
#          can get or scan QR codes and determine if someone is vaccinated.
import base64
import hashlib

import requests
from flask import Flask, request, render_template
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import socket
from pymongo import MongoClient
import gov_keys
from bs4 import BeautifulSoup
import qrcode
from bson.json_util import dumps, loads
import json
from cryptography.fernet import Fernet
import pickle

# Initializes Flask server and basic HTTP authentication
app = Flask(__name__, template_folder='gov_website')
auth = HTTPBasicAuth()

# For storing valid login credentials, this is for businesses
users = {
    "admin": generate_password_hash("secret"),
}


# HTTP Basic Auth reference: https://flask-httpauth.readthedocs.io/en/latest/
@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


# Landing page for the government website
@app.route("/", methods=['GET'])
def landing():
    result = {'country': 'US'}
    url = "https://www.worldometers.info/coronavirus/country/us/"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    results = soup.find_all(id='maincounter-wrap')  # finds the data in the html
    for r in results:
        title = r.text.split(":")
        if "Coronavirus Cases" in title[0]:
            result['Coronavirus Cases'] = int(title[1].replace(",", ""))
        elif "Deaths" == title[0].strip():
            result['Deaths'] = int(title[1].replace(",", ""))
        elif "Recovered" in title[0]:
            result['Recovered'] = int(title[1].replace(",", ""))

    client = MongoClient(
        "mongodb+srv://" + gov_keys.DATABASE_ADMIN_USERNAME + ":" + gov_keys.DATABASE_ADMIN_PASSWORD +
        "@cluster0.mm83g.mongodb.net/" +
        gov_keys.DATABASE_NAME + "?retryWrites=true&w=majority")
    db = client[gov_keys.DATABASE_NAME]
    collection = db[gov_keys.PATIENT_COLLECTION]
    return render_template("gov_landing_page.html", p1=str(result['Coronavirus Cases']),
                           p2=str(result['Deaths']),
                           p3=str(result['Recovered']),
                           p4=str(collection.count_documents({})))


# Flask server route for user getting QR code
@app.route("/individual", methods=['GET', 'PUT', 'POST'])
def individual():
    # Connect to MongoDB client, database, and collection
    client = MongoClient(
        "mongodb+srv://" + gov_keys.DATABASE_ADMIN_USERNAME + ":" + gov_keys.DATABASE_ADMIN_PASSWORD +
        "@cluster0.mm83g.mongodb.net/" +
        gov_keys.DATABASE_NAME + "?retryWrites=true&w=majority")
    db = client[gov_keys.DATABASE_NAME]
    collection = db[gov_keys.PATIENT_COLLECTION]

    if request.method == "POST":
        # Get name and DOB from website
        first_name = request.form.get("firstname")
        last_name = request.form.get("lastname")
        dob = request.form.get("dob")
        last_four_ssn = request.form.get("ssn")
        encryption_key = str(first_name + "_" + last_name + "_" + last_four_ssn + "_" + dob)
        hash_var = hashlib.md5(encryption_key.encode())
        gen_key = base64.urlsafe_b64encode(hash_var.hexdigest().encode())
        key = Fernet(gen_key)
        ssn = ".*" + last_four_ssn

        # Get entry from database
        records = collection.find({})
        record_found = False
        for r in records:
            try:
                key.decrypt(r['QRCodeData'].encode())
                query = {gov_keys.QR_CODE_ID: r['QRCodeData']}
                if r["NumIndividualRequests"] <= r["NumBusinessRequests"]:
                    collection.update_one(query, {
                        "$set": {"NumIndividualRequests": r["NumIndividualRequests"] + 1}})
                filepath = "static/" + r['QRCodeData'] + ".png"
                img = qrcode.make(r['QRCodeData'])
                img.save(filepath)
                return render_template("gov_output_qr.html", user_image=filepath)
            except:
                continue
        if not record_found:
            return "No Vaccination Record Found"

    return render_template("gov_get_qr.html")


# Flask server route for business scanning QR code
@app.route("/business", methods=['GET', 'PUT'])
@auth.login_required
def business():
    client = MongoClient(
        "mongodb+srv://" + gov_keys.DATABASE_ADMIN_USERNAME + ":" + gov_keys.DATABASE_ADMIN_PASSWORD +
        "@cluster0.mm83g.mongodb.net/" +
        gov_keys.DATABASE_NAME + "?retryWrites=true&w=majority")
    db = client[gov_keys.DATABASE_NAME]
    collection = db[gov_keys.PATIENT_COLLECTION]
    if (len(request.args)) == 0:
        return 'ACCESS DENIED: ' \
               'This endpoint should only be accessed from the Government Provided Tool, not from an internet url.'
    qr_param = request.args.get(gov_keys.QR_CODE_REQUEST_PARAM)
    query = {gov_keys.QR_CODE_ID: qr_param}
    collection_item = collection.find_one(query)
    if collection_item is None:
        return "No Vaccination Record Found"
    else:
        if collection_item["NumBusinessRequests"] == collection_item["NumIndividualRequests"]:
            return "Warning: Do not duplicate QR codes"
        collection.update_one(query, {"$set": {"NumBusinessRequests": collection_item["NumBusinessRequests"]+1}})
        return "Vaccination Record Found"


if __name__ == "__main__":
    app.run(host=socket.gethostbyname(socket.gethostname()), port=3001, debug=True, threaded=True)