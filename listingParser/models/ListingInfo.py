from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum
from typing import Any, Dict, List, Optional


class RentInfo(BaseModel):
    """Model for rent details."""
    price: float
    currency: str
    is_per_person: bool
    canBeShared: bool=None
    priceInCaseCanBeShared: float=None


class LocationInfo(BaseModel):
    """Model for location details."""
    address: str
    city: str
    state: str
    zip_code: str
    neighborhood: str


class ContactInfo(BaseModel):
    """Model for contact details."""
    phone_numbers: List[str]
    contact_method: str


class SecondaryContact(BaseModel):
    """Model for secondary contact details. If any"""
    name: str
    phone_number: str
    email: Optional[str] = None
    relationship: str=None


class CanBeSharedByTwoPeople:
    allowed:bool
    rent:RentInfo

class ListingStatus(str, Enum):
    """Enum for the status of a listing."""
    ACTIVE = "active"
    PENDING = "pending"
    RENTED = "rented"

class Listing(BaseModel):
    """Main model for the property listing."""
    property_type: str
    bedrooms: int
    bathrooms: int
    rent: RentInfo
    availability_date: date=None
    is_available: bool= True
    lease_terms: str
    location: LocationInfo
    amenities: List[str]
    preferences: str=None
    contact: ContactInfo
    is_duplicate: bool = False
    secondary_contacts: List[SecondaryContact] = Field(default_factory=list)
    extras: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="allow")
    inserted_on:date=date.today()
    listing_status: ListingStatus = ListingStatus.PENDING
