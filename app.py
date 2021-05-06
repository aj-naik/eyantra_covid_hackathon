from utils import generate_OTP, generate_token, get_beneficiaries, check_and_book, get_districts, get_pincodes, beep, \
    BENEFICIARIES_URL, WARNING_BEEP_DURATION
from flask import Flask, render_template, send_from_directory, request, session
from flask_session import Session
import traceback
from hashlib import sha256
from collections import Counter
from inputimeout import inputimeout, TimeoutOccurred
import tabulate
import copy
import time
import datetime
import requests
import sys
import os


app = Flask(__name__,static_folder='static')
app.config.from_object(__name__)
sess = Session()
request_header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}


@app.route('/', methods=["GET", "POST"])
def index():
    try:
        if request.method == "POST":
            global mobile
            global OTP
            global data
            global txdId
            global token
            global base_request_header
            global request_header

            mobile = request.form.get("mobile_number")
            base_request_header = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
            }
            time.sleep(10)
            OTP = request.form.get("otp")
            txnId = generate_OTP(mobile, base_request_header)
            token = generate_token(OTP, txnId, base_request_header)
            print(f'Token Generated: {token}')

            request_header = copy.deepcopy(base_request_header)
            request_header["Authorization"] = f"Bearer {token}"
            print("\n\n\nREACHED\n\n\n")
            session['request_header'] = request_header
           

    except Exception as e:
        print(str(e))
        print('Exiting Script')
        traceback.print_exc()

    return render_template("index.html")





headings = ("Beneficiary Reference ID","Name","Vaccine","Age","Status")
# table = (get_beneficiaries(request_header=request_header))



@app.route('/book', methods=["GET", "POST"])
def book():
    print(session['request_header'])
    print("Fetching registered beneficiaries.. ")
    tables = get_beneficiaries(session['request_header'])
    print("______________________________TYPE tables: ",type(tables),"_______________________________")
    data = tables
    
    print("______________________________TYPE data: ",type(data),"_______________________________")
    print("DATA: ",data)
    return render_template("book.html", headings = headings, data=data)



if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    sess.init_app(app)

    app.debug = True
    app.run()
