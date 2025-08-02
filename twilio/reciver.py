
import os
from twilio.rest import Client
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

from testing_MVP.twilio.TwilioMessage import TwilioMessage

load_dotenv(dotenv_path=Path(".twilio.env"))

account_sid = os.getenv("TWILIO_ACCOUNT_SID")  # ✅ Correctauth_token = os.getenv["TWILIO_ACCOUNT_KEY"]
auth_token = os.getenv("TWILIO_ACCOUNT_KEY")

client = Client(account_sid, auth_token)


def createMessage(message:str)->any:
    message = client.messages.create(
        body=message,
        from_="whatsapp:+14155238886",
        to="whatsapp:+12012386520",
    )

    return message

def parseMessage(formData)->TwilioMessage:
    message=TwilioMessage(**formData)
    return message



def getMessageInfo(message:TwilioMessage)->Optional[TwilioMessage]:
    message = client.messages(message.MessageSid).fetch()




