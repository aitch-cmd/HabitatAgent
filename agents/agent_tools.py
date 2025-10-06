from langchain.agents import tool




@tool
def search_accommodations(location: str, max_price: int, bedrooms: int):
    """
    Searches the database for available student accommodations.
    Use this tool when a user expresses intent to find, search for, or look for a place to live.
    
    Args:
        location (str): The city or neighborhood to search in. e.g., "Jersey City", "Downtown".
        max_price (int): The maximum monthly rent the user is willing to pay.
        bedrooms (int): The desired number of bedrooms.
    """
    print(f"\n---> TOOL CALLED: search_accommodations(location='{location}', max_price={max_price}, bedrooms={bedrooms})")
    # --- SIMULATED DATABASE SEARCH ---
    # In a real application, you would query your database here.
    return f"Simulated search complete. Found 2 apartments in {location} matching the criteria."

@tool
def add_listing(address: str, location: str, price: int, bedrooms: int, contact_email: str):
    """
    Adds a new property listing to the accommodation database.
    Use this tool when a user, such as an owner, landlord, or realtor, wants to list, add, or post a new property.
    
    Args:
        address (str): The full street address of the property.
        location (str): The city or neighborhood the property is in.
        price (int): The monthly rent for the property.
        bedrooms (int): The number of bedrooms in the property.
        contact_email (str): The email address for interested students to contact.
    """
    print(f"\n---> TOOL CALLED: add_listing(address='{address}', price={price}, contact_email='{contact_email}')")
    # --- SIMULATED DATABASE WRITE ---
    # In a real application, you would insert a new record into your database here.
    return f"Successfully added the property at {address} to the listings. Students will now be able to see it."