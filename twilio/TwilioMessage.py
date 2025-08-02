from pydantic import BaseModel

from typing import Optional

class TwilioMessage(BaseModel):
    ChannelPrefix: str
    ApiVersion:str
    MessageStatus:str
    SmsSid:str
    SmsStatus:str
    To:str
    From:str
    MessageSid:str
    AccountSid:str
    ChannelToAddress:str
    From: str
    ProfileName: Optional[str]
    MessageSid: str
    NumMedia: Optional[int] = 0
    MediaUrl0: Optional[str]
    MediaContentType0: Optional[str]



class TwilioSingleMessage(BaseModel):
