# Names: Garrett Campbell, Bryan Yowler
# Assignment: Final Project ECE 4564
# File: gov_server.py
# Purpose: Flask server used as the government website that users and businesses
#          can get or scan QR codes and determine if someone is vaccinated.

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

        # Get entry from database
        record_query = {
            "FirstName": first_name,
            "LastName": last_name,
            "DateOfBirth": dob
        }
        record = collection.find(record_query)

        if record is None:
            return "No Vaccination Record Found"
        else:
            json_list = list(record)
            json_record = dumps(json_list, indent=4)
            json_data = json.loads(json_record)

            # Make QR code and save
            filename = "static/your_qr.png"
            img = qrcode.make(json_data[0]['QRCodeData'])
            img.save(filename)
            full_filename = 'static/your_qr.png'
            return render_template("gov_output_qr.html", user_image=full_filename)

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
    collection_item = collection.find_one({gov_keys.QR_CODE_ID: request.args.get(gov_keys.QR_CODE_REQUEST_PARAM)})
    if collection_item is None:
        return "No Vaccination Record Found"
    else:
        # possibly update the QR to disable duplication
        return "Vaccination Record Found"


if __name__ == "__main__":
    app.run(host=socket.gethostbyname(socket.gethostname()), port=3001, debug=True, threaded=True)
