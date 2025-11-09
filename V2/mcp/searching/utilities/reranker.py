from typing import List, Dict
from sentence_transformers import SentenceTransformer, util
from rank_bm25 import BM25Okapi
import logging
import yaml

class HybridReranker:
    """
    HybridReranker ranks property listings using a combination of:
    
    1. **Semantic Similarity** (via embedding-based cosine similarity)
    2. **Keyword Relevance** (via BM25 keyword matching of user preferences)
    
    This reranker is intended to operate on a small candidate set (e.g., top 100 results)
    retrieved from MongoDB (or another datastore) using minimal hard filters.
    
    Attributes:
        embedder (SentenceTransformer): Used to compute dense embeddings for semantic scoring.
        alpha (float): Weight of semantic similarity score in the final ranking formula.
        beta (float): Weight of BM25-based keyword relevance score in the final ranking formula.
    
    Usage:
        >>> reranker = HybridReranker()
        >>> ranked_results = reranker.rerank(user_query, mongo_results)
    """
    
    @staticmethod
    def load_params(params_path: str) -> dict:
        """Load alpha and beta parameters from YAML config."""
        try:
            with open(params_path, 'r') as file:
                params = yaml.safe_load(file)
            logging.debug('Parameters retrieved from %s', params_path)
            return params
        except FileNotFoundError:
            logging.error('File not found: %s', params_path)
            raise
        except yaml.YAMLError as e:
            logging.error('YAML error: %s', e)
            raise
        except Exception as e:
            logging.error('Unexpected error: %s', e)
            raise

    CONFIG = load_params("V2/params.yaml")["primary_ranker"]

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 alpha: float = CONFIG["alpha"], beta: float = CONFIG["beta"]):
        """
        Initializes the hybrid reranker model.
        
        Args:
            model_name (str): HuggingFace/ SentenceTransformers model for embedding generation.
            alpha (float): Semantic similarity scoring weight.
            beta (float): BM25 keyword relevance scoring weight.
        """
        self.embedder = SentenceTransformer(model_name, device="cpu")
        self.alpha = alpha
        self.beta = beta

    def build_listing_text(self, c: Dict) -> str:
        """
        Converts a MongoDB listing document into a text blob for embedding and BM25 scoring.
        
        Fields included:
            - Title
            - Description
            - Bedroom/Bathroom info
            - Appliances and included utilities
            - Rental terms (fees and conditions)
        
        Args:
            c (dict): Listing data dictionary (MongoDB document).
        
        Returns:
            str: Concatenated text representing the listing.
        """
        title = c.get("title", "")
        description = c.get("description", "")
        bed_bath = f"{c.get('bedroom', '')} bedroom {c.get('bathroom', '')} bathroom"
        appliances = " ".join(c.get("amenities", {}).get("appliances", []))
        utilities = " ".join(c.get("amenities", {}).get("utilities_included", []))
        rental_terms = " ".join([str(v) for v in c.get("rental_terms", {}).values()])
        
        return f"{title} {description} {bed_bath} {appliances} {utilities} {rental_terms}"

    def rerank(self, user_query: Dict, candidates: List[Dict]) -> List[Dict]:
        """
        Reranks property candidates based on hybrid scoring:
        
        Scoring formula:
            final_score = alpha * semantic_similarity + beta * BM25_keyword_score
        
        Args:
            user_query (dict): Parsed search query with 'rag_content' holding preference keywords.
                               Example: {"rag_content": "furnished, balcony, pet friendly"}
            candidates (list): List of MongoDB candidate listing dictionaries.
        
        Returns:
            list: Sorted list of candidate listings (highest score first).
        """
        rag_content = user_query.get("rag_content", "").lower()
        preferences = [p.strip() for p in rag_content.split(",") if p.strip()]
        
        # Prepare candidate documents for BM25 (tokenized)
        corpus = [self.build_listing_text(c).lower().split() for c in candidates]
        bm25 = BM25Okapi(corpus)
        query_tokens = rag_content.split()
        bm25_scores = bm25.get_scores(query_tokens)
        
        # Semantic embedding of user preferences
        query_emb = self.embedder.encode(rag_content, convert_to_tensor=True)
        
        final_scores = []
        for idx, c in enumerate(candidates):
            text = self.build_listing_text(c)
            doc_emb = self.embedder.encode(text, convert_to_tensor=True)
            emb_score = util.cos_sim(query_emb, doc_emb).item()
            bm25_score = bm25_scores[idx]
            
            # Hybrid score
            final_score = self.alpha * emb_score + self.beta * bm25_score
            final_scores.append((final_score, c))
        
        final_scores.sort(reverse=True, key=lambda x: x[0])
        return [c for _, c in final_scores]


# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    user_message = {
        "location": "Greater Noida",
        "price": "",
        "rag_content": "pet friendly, balcony, furnished"
    }

    candidates = [
        {"title": "2BHK Apartment", "description": "Spacious, furnished, with balcony",
         "amenities": {"appliances": [], "utilities_included": []}, "bedroom": 2, "bathroom": 1},
        {"title": "Studio Flat", "description": "Affordable unit",
         "amenities": {"appliances": [], "utilities_included": []}, "bedroom": 1, "bathroom": 1},
        {"title": "3BHK Luxury", "description": "Pet friendly furnished apartment",
         "amenities": {"appliances": [], "utilities_included": []}, "bedroom": 3, "bathroom": 2},
    ]

    reranker = HybridReranker()
    reranked = reranker.rerank(user_message, candidates)

    for r in reranked:
        print(r["title"])
