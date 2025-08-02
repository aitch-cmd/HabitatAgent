from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import json

app = Flask(__name__)

@app.route("/capture_wa_message", methods=['POST'])
def reply_sms():
    # Create a new Twilio MessagingResponse

    multi_dict=request.form;

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


@app.route("/ping", methods=['GET'])
def ping():
    return Response("pong")


if __name__ == "__main__":
    app.run(port=3000)