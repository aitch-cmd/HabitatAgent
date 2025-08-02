from pydantic import BaseModel,Field
from datetime import datetime

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


#
# class SubresourceUris(BaseModel):
#     media: str
#
#
# class Tags(BaseModel):
#     campaign_name: str
#     message_type: str
#
#
# class MessageModel(BaseModel):
#     account_sid: str
#     api_version: str
#     body: str
#     date_created: datetime
#     date_sent: datetime
#     date_updated: datetime
#     direction: str
#     error_code: Optional[int] = None
#     error_message: Optional[str] = None
#     from_: str = Field(..., alias="from")  # 'from' is a reserved keyword
#     num_media: str
#     num_segments: str
#     price: Optional[str] = None
#     price_unit: Optional[str] = None
#     messaging_service_sid: str
#     sid: str
#     status: str
#     subresource_uris: SubresourceUris
#     tags: Tags
#     to: str
#     uri: str
#
#     class Config:
#         allow_population_by_field_name = True
#         from_attributes=True