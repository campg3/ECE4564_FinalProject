# Names: Garrett Campbell, Bryan Yowler
# Assignment: Final Project ECE 4564
# File: gov_server.py
# Purpose: Flask server used as the government website that users and businesses
#          can get or scan QR codes and determine if someone is vaccinated.
import base64
import hashlib
import matplotlib
import matplotlib.pyplot as plt
import requests
from flask import Flask, request, render_template
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import socket
from pymongo import MongoClient
import gov_keys
from bs4 import BeautifulSoup
import qrcode
from cryptography.fernet import Fernet
import uuid
import re
import shutil
import os
matplotlib.use("Agg")

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


# Page that shows data regarding new and active cases in the US today
# options to view a summary or data in specific states
@app.route("/today", methods=['GET', 'POST'])
def today():
    url = "https://www.worldometers.info/coronavirus/"
    us_endpoint = "country/us/"
    r = requests.get(url + us_endpoint)
    soup = BeautifulSoup(r.content, 'html.parser')

    # gets the names of the states
    name_results = soup.find_all(class_="mt_a")[:51]
    names_array = []
    for name in name_results:
        names_array.append(name.text)

    # gets the number of new cases for each state
    new_cases_results = soup.find_all("td", attrs={
        'style': re.compile(r'font-weight: bold; text-align:right;(background-color:#FFEEAA;)*')})[0:204:4]
    new_cases_array = []
    for n in new_cases_results:
        text = n.text.strip(" ")
        if text == "\n" or text == "":
            text = "0"
        new_cases_array.append(int(text.strip("").replace("+", "").replace(",", "")))

    # gets the number of active cases for each state
    active_num_results = soup.find_all("td", attrs={'style': 'text-align:right;font-weight:bold;'})[0:151:3]
    active_array = []
    for n in active_num_results:
        text = n.text.strip("\n").strip(" ")
        if text == "N/A" or text == "":
            text = "0"
        active_array.append(int(text.strip("").replace(",", "")))

    # creates the graph for a state upon individual request
    if request.method == "POST" and request.form.get("states") != "Summary":
        name = request.form.get("states")
        data = [new_cases_array[names_array.index(name)],
                active_array[names_array.index(name)]]
        names = ["New Cases (" + str(data[0]) + ")", "Active Cases (" + str(data[1])+ ")"]
        plt.bar(names, data)
        for i in range(2):
            plt.text(names[i],
                     data[i],
                     data[i], ha='center')
        plt.xlabel('States')
        plt.ylabel('Number of Cases')
        plt.yscale("log")
        plt.title('New Cases and Active Cases for ' + name)
        filename1 = "static/" + str(uuid.uuid4()) + ".png"
        plt.savefig(filename1)
        plt.clf()
        return render_template("gov_today_page.html",
                               user_image=filename1)

    # sorts the new cases and finds the top 10
    sorted_new = sorted(new_cases_array, reverse=True)[:10]
    sorted_names = []
    for i in sorted_new:
        sorted_names.append(names_array[new_cases_array.index(i)])

    # sorts the active cases and finds the top 10
    sorted_active = sorted(active_array, reverse=True)[:10]
    sorted_active_names = []
    for i in sorted_active:
        sorted_active_names.append(names_array[active_array.index(i)])

    # graphs the active cases and new cases graphs
    plt.bar(sorted_names, sorted_new)
    for i in range(len(sorted_names)):
        plt.text(sorted_names[i], sorted_new[i] // 2,
                 sorted_names[i] + " (" + str(sorted_new[i]) + ")", ha='center', rotation=90)
    plt.xlabel('States')
    plt.ylabel('Number of Cases')
    plt.title('Top 10 States based on number of new cases')
    plt.xticks([])
    filename1 = "static/" + str(uuid.uuid4()) + ".png"
    plt.savefig(filename1)
    plt.clf()

    plt.bar(sorted_active_names, sorted_active)
    for i in range(len(sorted_active_names)):
        plt.text(sorted_active_names[i], sorted_active[i] / 2,
                 sorted_active_names[i] + " (" + str(sorted_active[i]) + ")", ha='center', rotation=90)
    plt.xlabel('States')
    plt.ylabel('Number of Cases (millions)')
    plt.title('Top 10 States based on number of active cases')
    plt.xticks([])
    filename2 = "static/" + str(uuid.uuid4()) + ".png"
    plt.savefig(filename2)
    plt.clf()
    return render_template("gov_today_page.html",
                           user_image=filename1,
                           user_image1=filename2)


# Landing page for the government website, shows some simple US COVID stats
@app.route("/", methods=['GET'])
def landing():
    # extract data from the website for how many cases, deaths, and recoveries
    result = {'country': 'US'}
    url = "https://www.worldometers.info/coronavirus/"
    us_endpoint = "country/us/"
    r = requests.get(url + us_endpoint)
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

    # find how many vaccination records we have in order to display
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

    # if the request is based on the submission of the user's data to get the QR code,
    # grab the input info and query the database for it. If found, display the QR
    if request.method == "POST":
        # Get name and DOB from website
        first_name = request.form.get("firstname").strip()
        last_name = request.form.get("lastname").strip()
        dob = request.form.get("dob").strip()
        last_four_ssn = request.form.get("ssn").strip()

        # Make encryption key for searching database
        encryption_key = str(first_name + "_" + last_name + "_" + last_four_ssn + "_" + dob)
        hash_var = hashlib.md5(encryption_key.encode())
        gen_key = base64.urlsafe_b64encode(hash_var.hexdigest().encode())
        key = Fernet(gen_key)

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
        collection.update_one(query, {"$set": {"NumBusinessRequests": collection_item["NumBusinessRequests"] + 1}})
        return "Vaccination Record Found"


if __name__ == "__main__":
    app.run(host=socket.gethostbyname(socket.gethostname()), port=3001, debug=True, threaded=True)
