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

# Initializes Flask server and basic HTTP authentication
app = Flask(__name__, template_folder='gov_website')
auth = HTTPBasicAuth()

# For storing valid login credentials
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
                           p4=str(collection.count()))


# Flask server route for user getting QR code
@app.route("/user", methods=['GET', 'PUT', 'POST'])
def user():
    return "In user path"


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
    if collection.find_one({gov_keys.QR_CODE_ID: request.args.get(gov_keys.QR_CODE_REQUEST_PARAM)}) is None:
        return "No Vaccination Record Found"
    else:
        return "Vaccination Record Found"


if __name__ == "__main__":
    app.run(host=socket.gethostbyname(socket.gethostname()), port=3001, debug=True, threaded=True)
