from flask import Flask, render_template,jsonify, current_app, g, redirect, url_for, request, session,flash

import configparser
import boto3
import json
import os

import time
from flask_session import Session
from bokeh.plotting import figure, curdoc
import requests
from bokeh.embed import components
from bokeh.themes import LIGHT_MINIMAL, DARK_MINIMAL
import random
from twilio.rest import Client
from user_agents import parse
import configparser
import pymongo 
import os
from flask_simple_geoip import SimpleGeoIP
from db import *
# from db import add_comment, fin_user, transaction_log, transaction_log_find, profile_transaction,transaction_status_update, all_transaction, fin_user_login
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler
import pandas as pd

app = Flask(__name__)
app.secret_key = "super secret key"
app.config["SESSION_PERMANENT"] = False     # Sessions expire when the browser is closed
app.config["SESSION_TYPE"] = "filesystem" 





#config sample.ini
config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join("sample1.ini")))
# print(config['default']['aws_access_key_id'])
# print(config['default']['aws_secret_access_key'])
# AWS Bedrock runtime client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-west-2',  # Change if needed
    aws_access_key_id=config['default']['aws_access_key_id'],
    aws_secret_access_key=config['default']['aws_secret_access_key']
    
    
)




# Dashboard
@app.route("/dashboard")
def dashboard():
     # Scatter plot with random values
    x_values = list(range(10))
    y_values = [random.randint(1, 50) for _ in range(10)]

    p = figure(
        title="Carbon", 
        height=150, 
        sizing_mode="stretch_width"
    )

    curdoc().theme = 'carbon'
    curdoc().add_root(p)

    # p.circle(x_values, y_values, size=15, color="navy", alpha=0.5)
    p.line(x_values, y_values, line_color="navy", line_width=2)
    
    # Extract script and div components
    script, div = components(p)

    # Debugging: Print script and div to check if they are generated
    print("Generated Script:", script[:200])  # Print first 200 characters
    print("Generated Div:", div[:200])        # Print first 200 character
    return render_template('dashboard.html',script=script, div=div)





# monitoring 
@app.route("/monitoring")
def monitor():
    data = list(all_transaction())
    # print(data)
    table_list=[]
    for i in data:
        print(i)
        for j in i:
            table_list.append(j)
        break
    table_list=table_list[1::]
    # print(table_list)  

    # return render_template("profile.html",phone_number=session['number'],user_upi=session['upi'], table_list=table_list,data=data)
    return render_template('transactionMonitoring.html',table_list=table_list,data=data)



# Prompt template builder
def build_prompt(data):
    return f"""
You are a cybersecurity and fraud analysis expert AI. 

Based on the following transaction metadata, analyze and return a single JSON object with a risk score between 0 (no risk) and 1 (very high risk).

Use your understanding of common fraud patterns (like high amounts, suspicious IPs, failed logins, unfamiliar devices or locations).

Respond in this format: {{"risk_score": float}}

Transaction metadata:
Amount: {data['amount']}
Location (State): {data['location']}
IP Address: {data['ip']}
Device Type: {data['device_type']}
Login Attempt: {data['login_attempt']}
"""
# Amount: {data['amount']}
# Location (State): {data['location']}
# IP Address: {data['ip']}
# Device Type: {data['device_type']}
# Login Attempt: {data['login_attempt']}
@app.route("/risk-score", methods=["GET","POST"])
def risk_score():
    try:
        # input_data = request.get_json()
        data = transaction_log_find(session['trans_id'])
        print(data)
        input_data = {
            "amount": data['transaction_amount'],
            "location": 'Madhya Pradesh',
            "ip": '190.83.143.174',
            "device_type": 'Desktop',
            "login_attempt": 5
            }

        # Validate input fields
        required_fields = ['amount', 'location', 'ip', 'device_type', 'login_attempt']
        for field in required_fields:
            if field not in input_data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Build prompt
        prompt = build_prompt(input_data)

        # Claude 3 Sonnet request
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )

        # Parse response
        model_response = json.loads(response['body'].read().decode())
        assistant_msg = model_response['content'][0]['text'].strip()

        # Parse JSON result from Claude
        risk_result = json.loads(assistant_msg)
        print(risk_result['risk_score'])
        # return jsonify(risk_result)
        # session['risk_score']=risk_result['risk_score']

        transaction_risk_score_update(session['trans_id'],risk_result['risk_score'])
        return redirect(url_for('predict'))

    except Exception as e:
        return jsonify({"error": str(e)}), 500





# mock payments (FinPay)
@app.route("/payments", methods=['GET','POST'])
def payments():
    if request.method=='POST':
        g.start_time = time.perf_counter()
        upi_id=session["upi"]
        # data = request.get_json()
        # print(data)
        transaction_id= "TX"+str(random.randint(100,999))
        transaction_amount = request.form['amount']
        session["trans_id"]=transaction_id
        geoip_data = simple_geoip.get_geoip_data()
        # print(geoip_data['ip'])
        # user_ip=geoip_data['ip']
        user_ip="190.83.143.174"
        user_country="Madhya Pradesh"
        status="NULL"
        transaction_duration = 300
        total_time = time.perf_counter() - g.start_time
        time_in_ms = int(total_time * 1000)
        transaction_duration=time_in_ms
        print(transaction_duration)
        # device_type= session['device_type']
        device_type='Desktop'
        # print(risk_score)
        # risk_score=session['risk_score']
        # print(risk_score)
        risk_score=0
        transaction_log(upi_id,transaction_id,transaction_amount, transaction_duration,user_ip,user_country,status, risk_score,device_type)
        return redirect(url_for('risk_score'))
    
    
    print(session['number'])
    user_upi=session["upi"]

    return render_template('payments.html',user_upi=user_upi)
    


# Fraud Detection Model
@app.route("/predict",methods=['GET','POST'])
def predict():
    scaler = pickle.load(open("scaler.pkl", 'rb'))
    model = pickle.load(open("isolation_forest_model.pkl", 'rb'))
    # model = pickle.load(open("isolation_forest_model (1).pkl", 'rb'))
    # print(session['trans_id'])
    data = transaction_log_find(session['trans_id'])
    # print(data)
    # Transaction Duration (ms)', 'Transaction Amount', 'Login Attempt
    input_data = pd.DataFrame([{'TransactionAmount': int(data['transaction_amount']), 'TransactionDuration': int(data['transaction_duration']),'AccountBalance': 3000.00, 'LoginAttempt': 3}])
    
    
#     input_data = pd.DataFrame([
#     {'TransactionAmount': 1500.00, 'TransactionDuration': 45.0, 'AccountBalance': 3000.00, 'LoginAttempts': 1},
#     {'TransactionAmount': 9999.99, 'TransactionDuration': 10.0, 'AccountBalance': 500.00, 'LoginAttempts': 5},
#     {'TransactionAmount': 75.50, 'TransactionDuration': 360.0, 'AccountBalance': 200.00, 'LoginAttempts': 2},
#     {'TransactionAmount': 120.00, 'TransactionDuration': 240.0, 'AccountBalance': 5000.00, 'LoginAttempts': 1},
#     {'TransactionAmount': 5000.00, 'TransactionDuration': 20.0, 'AccountBalance': 6000.00, 'LoginAttempts': 0},
#     {'TransactionAmount': 60.00, 'TransactionDuration': 300.0, 'AccountBalance': 100.00, 'LoginAttempts': 3},
#     {'TransactionAmount': 700.00, 'TransactionDuration': 80.0, 'AccountBalance': 3500.00, 'LoginAttempts': 1},
#     {'TransactionAmount': 250.00, 'TransactionDuration': 180.0, 'AccountBalance': 1500.00, 'LoginAttempts': 1},
#     {'TransactionAmount': 18000.00, 'TransactionDuration': 5.0, 'AccountBalance': 100.00, 'LoginAttempts': 6},
#     {'TransactionAmount': 400.00, 'TransactionDuration': 90.0, 'AccountBalance': 2500.00, 'LoginAttempts': 2},
# ])

    # Fill missing values if any
    input_data = input_data.fillna(input_data.mean())
    scaler = StandardScaler()
    # X_scaled = scaler.fit_transform(X)
    # Scale and predict
    input_scaled = scaler.fit_transform(input_data)
    predictions = model.predict(input_scaled)

    # Interpret results
    outlier_mapping = {1: 'Potential Fraud', -1: 'Normal'}
    labels = [outlier_mapping[p] for p in predictions]
    print(labels)
    print(labels[0])
    if labels[0] == "Potential Fraud":
        trans_id=session["trans_id"]
        transaction_status_update(trans_id,"Blocked")
        return render_template("blocked.html", Fraud=labels[0])
    else:
        trans_id=session["trans_id"]
        transaction_status_update(trans_id,"Success")
        return render_template("success.html",Fraud=labels[0])


# home route
# @app.route("/")
# def welcome():
#     print("Connected")
#     add_comment(1,"Ohm shaanti Oshana","m@gmail.com","Superb","02.09.2025")

#     return "Success!"


# OTP Login
config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join("sample1.ini")))
print(config['Account SID']['SID'])
app.config.update(GEOIPIFY_API_KEY=config['GEO_API']['API'])

client = Client(config['Account SID']['SID'],config['Auth Token']['TOKEN'])


simple_geoip = SimpleGeoIP(app)
otp_storage ={}

def generate_otp():
    return str(random.randint(100000,999999))

def send_otp(phone_number, otp):
    message = client.messages.create(
        body=f'Your OTP is: {otp}',
        from_=config['Phone Number']['NUMBER'],
        to=phone_number
    )
    return message.sid


@app.route("/register", methods=['GET','POST'])
def register():
    if request.method == 'POST':
        session["number"] = "+91"+request.form['phone_number']
        phone_number="+91"+request.form['phone_number']
        otp = generate_otp()
        send_otp(phone_number,otp)
        otp_storage[phone_number]=otp

        return redirect(url_for('verify_otp_route', phone_number=phone_number))
    return render_template('register.html')

        


@app.route("/verify_otp",methods=['GET','POST'])
def verify_otp_route():
    if request.method=='POST':
        phone_number=session["number"]
        otp=request.form['otp']
        stored_otp=otp_storage.get(phone_number)
        if stored_otp and otp==stored_otp:
            upi_id=phone_number[3::]+"@okicicibank"
            print(upi_id)
            session["upi"]=upi_id
            geoip_data = simple_geoip.get_geoip_data()
            print(geoip_data['ip'])
            user_ip=geoip_data['ip']
            user_country=geoip_data['location']['country']
            flag=fin_user_login(phone_number)
            print(flag)
            print(fin_user_login(phone_number))
            user_agent = request.headers.get('User-Agent')
            user_agent_parsed = parse(user_agent)
            device_type = ("Mobile" if user_agent_parsed.is_mobile else
                        "Tablet" if user_agent_parsed.is_tablet else
                        "Desktop")
            if flag:
                print("Logged In")
                fin_user_update(phone_number,user_ip,user_country,device_type)
                return redirect(url_for('payments'))
            else:
                print("Registered")
                fin_user(phone_number,upi_id,user_ip,user_country,device_type)
                return redirect(url_for('payments'))

            
        else:
            # login_Attempt=login_Attempt+1
            flash('Invalid credentials.', 'error')
            return render_template("verifyOtp.html",phone_number=session['number'])
    return render_template("verifyOtp.html",phone_number=session['number'])


@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'POST':
        session["number"] = "+91"+request.form['phone_number']
        user_agent = request.headers.get('User-Agent')
        user_agent_parsed = parse(user_agent)
        device_type = ("Mobile" if user_agent_parsed.is_mobile else
                        "Tablet" if user_agent_parsed.is_tablet else
                        "Desktop")
        session['device_type']=device_type
        phone_number="+91"+request.form['phone_number']
        otp = generate_otp()
        send_otp(phone_number,otp)
        otp_storage[phone_number]=otp
        return redirect(url_for('verify_otp_route', phone_number=phone_number))
    return render_template('login.html')



@app.route("/profile")
def profile():
    data = list(profile_transaction(session['upi']))
    # print(data)
    table_list=[]
    for i in data:
        print(i)
        for j in i:
            table_list.append(j)
        break
    table_list=table_list[1::]
    # print(table_list)  

    return render_template("profile.html",phone_number=session['number'],user_upi=session['upi'], table_list=table_list,data=data)





if __name__ == "__main__":
    app.run(debug=True)
