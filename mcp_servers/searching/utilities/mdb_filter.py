import sys
from db.connection import MongoDBClient
from mcp_servers.searching.utilities.parser import UserMessageParser
from pymongo.errors import OperationFailure


class MongoDBFilter:
    def __init__(self, collection_name: str = "tulire_listings"):
        """Initialize DB connection and ensure indexes exist."""
        self.db_client = MongoDBClient(database_name="rental_database")
        self.collection = self.db_client.database[collection_name]

        try:
            self._ensure_indexes()
        except OperationFailure as e:
            print(f"⚠️ Index creation failed: {e}")

    def _ensure_indexes(self):
        """
        Ensure text index and numeric index exist.
        Avoid IndexOptionsConflict by checking existing indexes.
        """

        existing = self.collection.index_information()

        # ---------------------------
        # 1. HANDLE TEXT INDEX (ONE PER COLLECTION)
        # ---------------------------
        desired_text_fields = ["address", "title"]
        existing_text_index = None
        existing_text_fields = []

        # Detect existing text index
        for idx_name, idx_info in existing.items():
            if any(typ == "text" for _, typ in idx_info["key"]):
                existing_text_index = idx_name
                existing_text_fields = [field for field, typ in idx_info["key"] if typ == "text"]
                break

        # Case A — text index exists but missing fields → update
        if existing_text_index:
            if set(desired_text_fields) != set(existing_text_fields):
                print(f"🔧 Updating text index: {existing_text_index}")
                self.collection.drop_index(existing_text_index)

                self.collection.create_index(
                    [(field, "text") for field in desired_text_fields],
                    name="search_text_index"
                )
            else:
                print("✔ Text index already correct.")
        else:
            # Case B — no text index → create new
            print("🔧 Creating new combined text index.")
            self.collection.create_index(
                [(field, "text") for field in desired_text_fields],
                name="search_text_index"
            )

        # ---------------------------
        # 2. HANDLE NUMERIC INDEX (rent_price)
        # ---------------------------
        numeric_index_exists = False

        for idx_name, idx_info in existing.items():
            if idx_info["key"] == [("rent_price", 1)]:
                numeric_index_exists = True
                break

        if not numeric_index_exists:
            print("🔧 Creating numeric index: rent_price")
            self.collection.create_index(
                [("rent_price", 1)],
                name="rent_price_1"
            )
        else:
            print("✔ Numeric index already exists: rent_price_1")

    # -------------------------
    # QUERY BUILDING
    # -------------------------
    def build_query(self, parsed_message: dict) -> dict:
        """Build MongoDB query using extracted info."""
        query = {}

        if parsed_message.get("location"):
            query["$text"] = {"$search": parsed_message["location"]}

        # Rent price filter
        if parsed_message.get("price"):
            try:
                price_str = "".join(ch for ch in str(parsed_message["price"]) if ch.isdigit())
                if price_str:
                    price_val = int(price_str)
                    query["rent_price"] = {"$lte": price_val}
            except (ValueError, TypeError):
                print(f"Invalid price value: {parsed_message['price']}")

        return query

    # -------------------------
    # SEARCH FUNCTION
    # -------------------------
    def search_rentals(self, user_message: str):
        """Parse user message, build query, and fetch matching rentals."""
        parser = UserMessageParser()
        parsed = parser.extract(user_message)

        print("\nParsed message:", parsed)
        query = self.build_query(parsed)
        print("🔎 MongoDB Query:", query)

        results = list(self.collection.find(query))

        if not results:
            print("No listings found for this query.")

        return results


if __name__ == "__main__":
    executor = MongoDBFilter()

    # Example messages for testing
    test_messages = [
        "Looking for a 1BHK flat in South Orange under 2200"
    ]

    for msg in test_messages:
        print("\n💬 User Input:", msg)
        listings = executor.search_rentals(msg)

        print("📌 Matching Listings:")
        for l in listings:
            print(l)
