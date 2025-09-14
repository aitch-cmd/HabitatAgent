from models.ListingInfo import Listing


class CatchDuplicateListings:
    def __init__(self):
        pass  # In case you add instance-level data later

    def normalize(self, text):
        """Converts text to lowercase and removes extra whitespace"""
        return text.strip().lower()

    def getDuplicateListingQuery(self,new_listing:Listing):
        query = {
            "location.address": new_listing.location.address,
            "location.city": new_listing.location.city,
            "location.state": new_listing.location.state,
            "location.zip_code": new_listing.location.zip_code,
        }

        return query

    def calculate_similarity_score(self, new, existing):
        score = 0
        max_score = 5

        # Address match
        if self.normalize(new['location']['address']) == self.normalize(existing['location']['address']):
            score += 2
        elif self.normalize(new['location']['neighborhood']) == self.normalize(existing['location']['neighborhood']):
            score += 1

        # Contact match
        if new['contact']['phone_numbers'][0] in existing['contact']['phone_numbers']:
            score += 1

        # Rent similarity
        rent_diff = abs(float(new['rent']['price']) - float(existing['rent']['price']))
        if rent_diff <= 100:
            score += 1

        # Room type similarity
        if self.normalize(new['property_type']) == self.normalize(existing['property_type']):
            score += 1

        return score, max_score

    def is_similar_listing(self, new_listing, all_existing_listings, threshold_ratio=0.8):
        for existing in all_existing_listings:
            score, max_score = self.calculate_similarity_score(new_listing, existing)
            similarity_ratio = score / max_score
            if similarity_ratio >= threshold_ratio:
                return True, existing
        return False, None
