import asyncio
from typing import Any
from mcp.server.fastmcp import FastMCP
from V2.mcp.searching.utilities.parser import UserMessageParser
from V2.mcp.searching.utilities.mdb_filter import MongoDBFilter
from V2.mcp.searching.utilities.reranker import HybridReranker
import json

# Initialize FastMCP server
mcp = FastMCP("property-search")

class PropertySearchPipeline:
    """
    Unified pipeline for property search:
    1. Parse user message (extract location, price, preferences)
    2. MongoDB filter (hard constraints: location, price, bedrooms)
    3. Hybrid reranker (semantic + keyword matching)
    """
    
    def __init__(self):
        # Initialize all components using your existing code
        self.message_parser = UserMessageParser()
        self.mongo_filter = MongoDBFilter(collection_name="tulire_listings")
        self.hybrid_reranker = HybridReranker()
        
    def search(self, user_message: str, top_k: int = 5) -> list[dict]:
        """
        Execute the full search pipeline.
        
        Args:
            user_message: Natural language query from user
            top_k: Number of top results to return (default: 10)
            
        Returns:
            List of ranked property listings
        """
        try:
            # Step 1: Parse user message into structured fields
            parsed_message = self.message_parser.extract(user_message)
            print(f"📝 Parsed: {parsed_message}")
            
            # Step 2: MongoDB query with hard filters
            # Use the build_query method from your MongoDBFilter
            mongo_query = self.mongo_filter.build_query(parsed_message)
            print(f"🔍 MongoDB Query: {mongo_query}")
            
            # Execute MongoDB search
            candidates = list(self.mongo_filter.collection.find(mongo_query))
            print(f"📊 Retrieved {len(candidates)} candidates from MongoDB")
            
            # If no candidates found, return empty list
            if not candidates:
                return []
            
            # Step 3: Apply hybrid reranking if we have preferences
            rag_content = parsed_message.get("rag_content", "").strip()
            
            if rag_content and len(candidates) > 1:
                # Rerank using semantic similarity + keyword matching
                ranked_candidates = self.hybrid_reranker.rerank(
                    user_query=parsed_message,
                    candidates=candidates
                )
                print(f"✅ Reranked {len(ranked_candidates)} results")
            else:
                # No preferences or only 1 result - skip reranking
                ranked_candidates = candidates
                print("⚠️ Skipped reranking (no preferences or single result)")
            
            # Step 4: Return top K results
            final_results = ranked_candidates[:top_k]
            
            return final_results
            
        except Exception as e:
            print(f"❌ Error in search pipeline: {e}")
            raise


# Initialize the pipeline once (singleton pattern)
_pipeline = PropertySearchPipeline()


@mcp.tool()
def search_properties(user_query: str, max_results: int = 10) -> str:
    """
    Search for rental properties based on natural language query.
    
    This tool performs:
    1. Message parsing (extracts location, price, preferences)
    2. MongoDB filtering (location, price range, bedroom count)
    3. Hybrid reranking (semantic similarity + keyword matching)
    
    Args:
        user_query: Natural language search query (e.g., "2BHK furnished near MIT under 25k")
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        JSON string containing ranked property listings
        
    Examples:
        - "Find 2BHK apartments in Bangalore under 20000"
        - "3BHK furnished flat with parking near MG Road"
        - "Studio apartment pet friendly under 15k"
    """
    try:
        # Execute the search pipeline
        results = _pipeline.search(user_query, top_k=max_results)
        
        # Format results for output
        if not results:
            return json.dumps({
                "status": "success",
                "message": "No properties found matching your criteria",
                "count": 0,
                "results": []
            }, indent=2)
        
        # Clean up results - remove MongoDB _id field for cleaner output
        cleaned_results = []
        for listing in results:
            # Convert ObjectId to string if present
            if "_id" in listing:
                listing["_id"] = str(listing["_id"])
            cleaned_results.append(listing)
        
        # Return formatted JSON response
        return json.dumps({
            "status": "success",
            "message": f"Found {len(cleaned_results)} matching properties",
            "count": len(cleaned_results),
            "query": user_query,
            "results": cleaned_results
        }, indent=2, ensure_ascii=False)
        
    except Exception as e:
        # Return error in structured format
        return json.dumps({
            "status": "error",
            "message": f"Search failed: {str(e)}",
            "count": 0,
            "results": []
        }, indent=2)


@mcp.tool()
def get_property_summary(user_query: str, max_results: int = 5) -> str:
    """
    Search properties and return a concise summary suitable for chat responses.
    
    Similar to search_properties but returns a more readable text summary
    instead of full JSON data.
    
    Args:
        user_query: Natural language search query
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        Human-readable summary of top properties
        
    Example Output:
        "Found 3 properties:
        1. 2BHK Apartment in Koramangala - ₹22,000/month
        2. 2BHK Furnished Flat near MIT - ₹24,000/month
        3. ..."
    """
    try:
        # Execute search
        results = _pipeline.search(user_query, top_k=max_results)
        
        if not results:
            return "No properties found matching your criteria. Try adjusting your search parameters."
        
        # Build human-readable summary
        summary_lines = [f"Found {len(results)} matching properties:\n"]
        
        for idx, listing in enumerate(results, 1):
            title = listing.get("title", "Untitled Property")
            price = listing.get("rent_price", "Price not available")
            bedrooms = listing.get("bedroom", "N/A")
            location = listing.get("location", "Location not specified")
            
            # Format price
            if isinstance(price, (int, float)):
                price_str = f"₹{price:,.0f}/month"
            else:
                price_str = str(price)
            
            summary_lines.append(
                f"{idx}. {title} - {bedrooms} BHK in {location} - {price_str}"
            )
        
        return "\n".join(summary_lines)
        
    except Exception as e:
        return f"Error searching properties: {str(e)}"


# Optional: Add a health check tool
@mcp.tool()
def check_search_status() -> str:
    """
    Check if the property search service is operational.
    
    Returns:
        Status message with component health
    """
    try:
        # Test MongoDB connection
        db_status = "Connected" if _pipeline.mongo_filter.collection else "Disconnected"
        
        # Test reranker
        reranker_status = "Loaded" if _pipeline.hybrid_reranker.embedder else "Not Loaded"
        
        # Get collection count
        total_listings = _pipeline.mongo_filter.collection.count_documents({})
        
        return json.dumps({
            "status": "operational",
            "components": {
                "mongodb": db_status,
                "hybrid_reranker": reranker_status,
                "message_parser": "Active"
            },
            "database": {
                "total_listings": total_listings,
                "collection": "tulire_listings"
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


# Run the MCP server
if __name__ == "__main__":
    mcp.run()