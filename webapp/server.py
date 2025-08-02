import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify
from sqlalchemy.dialects.mysql import DATETIME
from twilio.twiml.messaging_response import MessagingResponse
from twilio_service.reciver import getSingleMessageInfo,parseMessage
from datetime import date
from datetime import datetime



load_dotenv(dotenv_path=Path(".env"))
app = Flask(__name__)

@app.route("/capture_wa_message", methods=['POST'])
def reply_sms():

    try:
    # Create a new Twilio MessagingResponse
        twilioMessageNotification=parseMessage(request.data)
        messgaeInfo=getSingleMessageInfo(twilioMessageNotification)
        print(messgaeInfo)



        multi_dict=request.form

        body = request.form.get("Body")  # Text message content
        from_number = request.form.get("From")  # Sender's WhatsApp number
        profile_name = request.form.get("ProfileName")  # Sender's profile name
        message_sid = request.form.get("MessageSid")  # Unique ID for message

        print("==== Incoming Message ====")
        print("From:", from_number)
        print("Name:", profile_name)
        print("Message SID:", message_sid)
        print("Body:", body)
        print("===========================")

        resp = MessagingResponse()
        resp.message("The Robots are coming! Head for the hills!")

        # Return the TwiML (as XML) response
        return Response(str(resp), mimetype='text/xml')
    except Exception as ex:
        return Response(ex, mimetype='text/xml')

@app.route("/ping", methods=['GET'])
def ping():
    today = datetime.now()
    return jsonify({"date": today})


if __name__ == "__main__":
    print(os.environ.get("PORT"))
    app.run(port=int(os.environ.get("PORT", 8080)))