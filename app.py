from flask import Flask, render_template, send_from_directory, request
from hashlib import sha256
from collections import Counter
from inputimeout import inputimeout, TimeoutOccurred
import tabulate, copy, time, datetime, requests, sys, os
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
app.config["DEBUG"] = False
from utils import generate_token_OTP, get_beneficiaries, check_and_book, get_districts, get_pincodes, beep, \
    BENEFICIARIES_URL, WARNING_BEEP_DURATION

@app.route('/', methods=["GET", "POST"])
def index():
    try:
        if request.method == "POST":
            formid = request.args.get('formid', 1, type=int)
            if formid == 1:
                global mobile
                mobile = request.form.get("mobile_number")
                request_header = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
                }
                # token = generate_token_OTP(mobile, request_header)
                data = {"mobile": mobile,
        "secret": "U2FsdGVkX1+b2/jGHLoV5kD4lpHdQ/CI7p3TnigA+6ukck6gSGrAR9aAuWeN/Nod9RrY4RaREfPITQfnqgCI6Q=="}
                print(f"Requesting OTP with mobile number {mobile}..")
                txnId = requests.post(url='https://cdn-api.co-vin.in/api/v2/auth/generateMobileOTP', json=data, headers=request_header)

                if txnId.status_code == 200:
                    txnId = txnId.json()['txnId']
                else:
                    print('Unable to Create OTP')
                    print(txnId.text)
                    os.system("pause")

                time.sleep(10)

                OTP = request.form.get("otp")
                print("###########    OTP:  ",OTP)
                print("###########   MObile:", mobile)
                data = {"otp": sha256(str(OTP).encode('utf-8')).hexdigest(), "txnId": txnId}
                print(f"Validating OTP..")

                token = requests.post(url='https://cdn-api.co-vin.in/api/v2/auth/validateMobileOtp', json=data, headers=request_header)
                if token.status_code == 200:
                    token = token.json()['token']
                else:
                    print('Unable to Validate OTP')
                    print(token.text)
                    os.system("pause")

                print(f'Token Generated: {token}')

                request_header = copy.deepcopy(request_header)
                request_header["Authorization"] = f"Bearer {token}"
                # Get Beneficiaries
                print("Fetching registered beneficiaries.. ")
                beneficiary_dtls = get_beneficiaries(request_header)
                
            if len(beneficiary_dtls) == 0:
                print("There should be at least one beneficiary. Exiting.")
                os.system("pause")
                sys.exit(1)

            # Make sure all beneficiaries have the same type of vaccine
            vaccine_types = [beneficiary['vaccine'] for beneficiary in beneficiary_dtls]
            vaccines = Counter(vaccine_types)

            if len(vaccines.keys()) != 1:
                print(f"All beneficiaries in one attempt should have the same vaccine type. Found {len(vaccines.keys())}")
                os.system("pause")
                sys.exit(1)

            print("\n================================= Location Info =================================\n")

            search_option = input("""Search by Pincode? Or by State/District? \nEnter 1 for Pincode or 2 for State/District. (Default 2) : """)
            search_option = int(search_option) if int(search_option) in [1, 2] else 2

            if search_option == 2:
                # Collect vaccination center preferance
                location_dtls = get_districts(request_header)

            else:
                # Collect vaccination center preferance
                location_dtls = get_pincodes()

            print("\n================================= Additional Info =================================\n")

            # Set filter condition
            minimum_slots = input(f'Filter out centers with availability less than ? Minimum {len(beneficiary_dtls)} : ')
            if minimum_slots:
                minimum_slots = int(minimum_slots) if int(minimum_slots) >= len(beneficiary_dtls) else len(beneficiary_dtls)
            else:
                minimum_slots = len(beneficiary_dtls)

            # Get refresh frequency
            refresh_freq = input('How often do you want to refresh the calendar (in seconds)? Default 15. Minimum 5. : ')
            refresh_freq = int(refresh_freq) if refresh_freq and int(refresh_freq) >= 5 else 15

            print("\n=========== CAUTION! =========== CAUTION! CAUTION! =============== CAUTION! =======\n")
            print(" ==== BE CAREFUL WITH THIS OPTION! AUTO-BOOKING WILL BOOK THE FIRST AVAILABLE CENTRE, DATE, AND SLOT! ==== ")
            auto_book = input("Do you want to enable auto-booking? (yes-please or no): ")

            token_valid = True
            while token_valid:
                request_header["Authorization"] = f"Bearer {token}"

                # call function to check and book slots
                token_valid = check_and_book(request_header, beneficiary_dtls, location_dtls, search_option,
                                            min_slots=minimum_slots,
                                            ref_freq=refresh_freq,
                                            auto_book=auto_book)

                # check if token is still valid
                beneficiaries_list = requests.get(BENEFICIARIES_URL, headers=request_header)
                if beneficiaries_list.status_code == 200:
                    token_valid = True

                else:
                    # if token invalid, regenerate OTP and new token
                    beep(WARNING_BEEP_DURATION[0], WARNING_BEEP_DURATION[1])
                    print('Token is INVALID.')
                    token_valid = False

                    tryOTP = input('Try for a new Token? (y/n): ')
                    if tryOTP.lower() == 'y':
                        if mobile:
                            tryOTP = input(f"Try for OTP with mobile number {mobile}? (y/n) : ")
                            if tryOTP.lower() == 'y':
                                token = generate_token_OTP(mobile, request_header)
                                token_valid = True
                            else:
                                token_valid = False
                                print("Exiting")
                        else:
                            mobile = input(f"Enter 10 digit mobile number for new OTP generation? : ")
                            token = generate_token_OTP(mobile, request_header)
                            token_valid = True
                    else:
                        print("Exiting")
                        os.system("pause")

    except Exception as e:
        print(str(e))
        print('Exiting Script')
        os.system("pause")
            
       # getting input with name = lname in HTML form
        # if formid == 2:

            
            


    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
