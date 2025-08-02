
import os
from twilio.rest import Client
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional
from twilio.rest.api.v2010.account.message import MessageInstance
from twilio.base.exceptions import TwilioRestException
load_dotenv(dotenv_path=Path(".twilio.env"))
from twilio_service.TwilioMessage import TwilioMessage

account_sid = os.getenv("TWILIO_ACCOUNT_SID")  # ✅ Correctauth_token = os.getenv["TWILIO_ACCOUNT_KEY"]
auth_token = os.getenv("TWILIO_ACCOUNT_KEY")

client = Client(account_sid, auth_token)


def createMessage(message:str)->MessageInstance:

    try:
        message = client.messages.create(
            body=message,
            from_="whatsapp:+14155238886",
            to="whatsapp:+12012386520",
        )
        return message
    except TwilioRestException as e:
        print("f COuld not create messages")
        return None

def parseMessage(formData:dict)->TwilioMessage:
    message=TwilioMessage(**formData)
    return message

def getSingleMessageInfo(message:TwilioMessage)->Optional[MessageInstance]:
    info =  client.messages(message.MessageSid).fetch()
    return info








