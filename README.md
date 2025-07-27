### MVP Feature Focus: Room-Finding Chatbot

Here's a list of essential features I recommend for your MVP, focusing on the core problem of connecting users with relevant room listings and streamlining the initial information exchange. This aims to deliver significant value without overcomplicating the first iteration.

1. **Automated Listing Ingestion & Parsing:**
    - **Goal:** Automatically capture new room listings posted in the WhatsApp group.
    - **Details:** The bot should be able to identify new messages containing listing information. It needs to **parse key data points** from these messages like:
        - **Room Type:** (e.g., private room, shared room, entire apartment)
        - **Basic Location:** (e.g., neighborhood, street if provided – keep it simple for MVP, maybe just "Jersey City" if specific street isn't consistent)
        - **Price:** (e.g., "$800/month")
        - **Key Features Mentioned:** (e.g., "private bath," "furnished," "utilities included")
    - **Why it's MVP:** This is the absolute foundation. Without parsing the data, the bot can't do anything else.
2. **User Preference Collection:**
    - **Goal:** Allow users looking for rooms to tell the bot what they're searching for.
    - **Details:** When a user initiates a conversation (e.g., "Hi, I'm looking for a room"), the bot should ask a few essential questions:
        - "What's your **budget range**?" (e.g., "$700-$1000")
        - "Are you looking for a **private room, shared room, or entire place**?"
        - "Are there any **must-have features**?" (e.g., "private bathroom," "pet-friendly" – limited options for MVP)
        - For location, since we know your current location is Jersey City, it could ask "Are you looking in a specific part of **Jersey City**?" or default to "anywhere in Jersey City" for now.
    - **Why it's MVP:** This enables the core value proposition: personalization and matching.
3. **Basic Matching & Recommendation:**
    - **Goal:** Present relevant listings to users based on their collected preferences.
    - **Details:** After collecting preferences, the bot will compare them against the parsed listing data and provide a **short list (e.g., 3-5) of the best matches**. Each recommendation should include:
        - The **original message/summary** of the listing.
        - A **direct way for the user to express interest** (e.g., "Reply 'Interested [Listing Number]' to connect with the poster").
    - **Why it's MVP:** This is the "aha!" moment for users – seeing that the bot can actually find what they're looking for.
4. **Direct Contact Facilitation:**
    - **Goal:** Enable interested users to easily get in touch with the original poster.
    - **Details:** When a user expresses interest in a specific listing, the bot should **provide the contact information of the original poster** (e.g., "Great! You can message [Original Poster's Name/Number] directly for more details or to arrange a viewing.")
    - **Why it's MVP:** This bridges the gap and allows the human-to-human interaction to take over, which is sufficient for an MVP and avoids the complexity of automated scheduling right away.
