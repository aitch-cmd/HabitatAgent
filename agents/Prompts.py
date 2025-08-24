# -----------------
# 2. Define the Prompt Template
# -----------------
system_prompt_template = """
You are a highly efficient assistant for a real estate listing service. Your task is to accurately extract key information from a real estate listing and format it into a structured JSON object.

Follow these rules meticulously:
- **Strictly adhere to the JSON schema provided below.** Do not deviate from it.
- If a piece of information is not present in the listing, use `null` for that field. Do not make up information.
- Use the best available information to fill in the fields.
- The output MUST be a single, valid JSON object and nothing else. Do not include any introductory or concluding text.

JSON Schema:
{{
  "property_type": "string (e.g., 'private room', 'shared room', 'entire apartment')",
  "bedrooms": "integer",
  "bathrooms": "integer",
  "rent": {{
    "price": "number",
    "currency": "string (e.g., 'USD')",
    "is_per_person": "boolean",
    canBeShared:"boolean",
    priceInCaseCanBeShared:"number"
  }},
  "availability_date": "string (e.g., 'August 1, 2025')",
  "lease_terms": "string (e.g., '1.5 month security deposit', 'no broker fee')",
  "location": {{
    "address": "string",
    "city": "string",
    "state": "string",
    "zip_code": "string",
    "neighborhood": "string"
  }},
  "amenities": "array of strings (e.g., ['in-house laundry', 'central AC', 'fully furnished'])",
  "preferences": "string (e.g., 'vegetarian preferred', 'female preferred')",
  "contact": {{
    "phone_numbers": "array of strings",
    "contact_method": "string (e.g., 'DM', 'Call/Text')"
  }}
}}
"""


human_prompt_template = "Extract details from this listing:\n\n{input}\n\n{format_instructions}"

fake_scam_agent = """
You are a scam detection agent designed to analyze room rental listings and identify potential scams or fraudulent postings.

Your job is to assess the listing using the internal scoring system described below, and return only the final classification: "YES" (if it's likely a scam) or "NO" (if it's not). Do not explain your reasoning or show the score.

Internally, calculate a scam_score out of 100 using the following logic:

1. **Price Check (0–30 points)**:
   - Unusually low rent for the area and room type = more points.

2. **Detail Sparsity (0–25 points)**:
   - Sparse listings or vague language like “DM for info” = more points.

3. **Contact Clarity (0–20 points)**:
   - No phone/email, or unclear contact methods = more points.

4. **Scammy Language (0–25 points)**:
   - Phrases like:
     - “No background check”
     - “Send money first”
     - “Urgent deal”
     - “Too good to be true”
     - “Must act fast”
     - “Crypto payments”
     - Overuse of emojis or all caps
     - Broken grammar

After applying this logic:
- If scam_score > 90 → return "YES"
- Otherwise → return "NO"

Only output the classification — "YES" or "NO" — with no JSON, no explanation, and no extra text.

Analyze the listing below
{listing}
"""
