from flask import Blueprint, request, Response, jsonify
from twilio.twiml.messaging_response import MessagingResponse

from listingParser.HouseParser import extractDetails
from twilio_service.reciver import getSingleMessageInfo, parseMessage

whatsapp_bp = Blueprint("whatsapp", __name__)



@whatsapp_bp.route("/capture_wa_message", methods=['POST'])
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


@whatsapp_bp.route("/mock/capture_wa_message", methods=['POST'])
def mock_sms():
        twilioMessageNotification=parseMessage(request.data)
        return jsonify({"status":"success","data":twilioMessageNotification.dict()})