from pydantic import BaseModel
from typing import List


class RentInfo(BaseModel):
    """Model for rent details."""
    price: float
    currency: str
    is_per_person: bool


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


class Listing(BaseModel):
    """Main model for the property listing."""
    property_type: str
    bedrooms: int
    bathrooms: int
    rent: RentInfo
    availability_date: str
    lease_terms: str
    location: LocationInfo
    amenities: List[str]
    preferences: str
    contact: ContactInfo
    is_duplicate: bool = False
