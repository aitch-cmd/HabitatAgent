HabitatAgent
A sophisticated property management platform built on the MCP (Model Context Protocol) and A2A (Agent-to-Agent) architecture, featuring an intelligent orchestrator that delegates tasks to specialized AI agents for seamless rental workflow automation.
Architecture Overview
The system employs a host-agent orchestrator pattern where a central coordinator intelligently routes requests to three specialized agents:
┌─────────────────────────────────────────────────────────┐
│                   Orchestrator Agent                     │
│          (Intent Recognition & Task Routing)             │
└──────────────────┬──────────────────┬───────────────────┘
                   │                  │                    
         ┌─────────┴────────┐  ┌─────┴──────┐  ┌─────────┴────────┐
         │  Search Agent    │  │   Listing  │  │   Alert Agent    │
         │   (Port 8003)    │  │   Agent    │  │   (Port 8005)    │
         │                  │  │(Port 8004) │  │                  │
         │ Property Search  │  │  Property  │  │  Real-time       │
         │ NLP + Reranking  │  │  Creation  │  │  Notifications   │
         └──────────────────┘  └────────────┘  └──────────────────┘
                   │                  │                    │
                   └──────────────────┴────────────────────┘
                                      │
                            ┌─────────┴─────────┐
                            │   MongoDB Atlas    │
                            │  rental_database   │
                            └───────────────────┘
                                      │
                            ┌─────────┴─────────┐
                            │   MCP Servers      │
                            │ Ports 9000-9002    │
                            └───────────────────┘
Key Features
Intelligent Orchestration

Intent-based routing: Automatically identifies user intent (search/list/alert) and delegates to the appropriate agent
Zero-shot classification: Handles ambiguous queries with clarifying questions
Seamless handoffs: Maintains context across agent boundaries using A2A protocol

Advanced Property Search (Search Agent)

Natural Language Processing: Understands queries like "2BHK near MIT under $2500 with parking"
Hybrid Reranking Engine: Combines semantic similarity (60%) + keyword matching (40%) for contextually relevant results
MongoDB Aggregation: Optimized queries with text search and price range constraints
Sub-second response times designed to scale to 5,000+ listings

Automated Listing Creation (Listing Agent)

Conversational Interface: Accepts unstructured property descriptions in any format
AI-powered Parsing: Uses OpenAI GPT-4o-mini to extract structured data from casual text
85% Time Reduction: Auto-parses and validates listings without manual data entry
One-shot creation: Parse → Validate → Save workflow with instant confirmation

Real-Time Alert System (Alert Agent)

MongoDB Change Streams: Monitors new listings in real-time (no polling)
Instant Notifications: Email alerts sent within 3 seconds of matching listings
Flexible Criteria: Location-based + price-based filtering with partial matching
Multi-alert Support: Users can set multiple concurrent alerts

Performance Metrics
MetricAchievementListing Creation Time85% reduction (from manual entry to auto-parse)Search Response TimeSub-second for 5,000+ listingsAlert Latency<3 seconds from listing insert to email sentScalabilityDesigned for 5,000+ properties with horizontal scaling
Technology Stack
Core Framework

MCP (Model Context Protocol): FastMCP v2.13+ for agent-tool communication
A2A Protocol: Agent-to-agent delegation with stateless HTTP transport (a2a-sdk v0.3+)
Google ADK: Agent orchestration and coordination (v1.18+)

AI/ML Components

OpenAI GPT-4o-mini: Natural language understanding and data extraction
Sentence Transformers: all-MiniLM-L6-v2 for semantic similarity
BM25: Keyword-based relevance scoring (rank-bm25)
Custom NLP Parser: Multi-stage query understanding pipeline

Backend Infrastructure

MongoDB Atlas: Primary database with replica set for change streams
Change Streams: Real-time data synchronization
Email Service: SMTP-based notification delivery (Gmail)
PyMongo 4.15+: MongoDB driver with async support

Development

Python 3.12: Core language
asyncio: Asynchronous operation handling
Uvicorn: ASGI server for agent hosting
LangChain: LLM orchestration and prompt management

Project Structure
HabitatAgent/
├── agents/                              # A2A Agent implementations
│   ├── host/                            # Orchestrator agent (Port 8001)
│   │   ├── __main__.py                  # Agent server entry point
│   │   ├── agent.py                     # Core orchestration logic
│   │   ├── agent_executor.py            # A2A execution wrapper
│   │   ├── descriptions.txt             # Agent description
│   │   └── instructions.txt             # System prompts
│   ├── search/                          # Property search agent (Port 8003)
│   │   ├── __main__.py
│   │   ├── agent.py
│   │   ├── agent_executor.py
│   │   ├── descriptions.txt
│   │   └── instructions.txt
│   ├── listings/                        # Listing creation agent (Port 8004)
│   │   ├── __main__.py
│   │   ├── agent.py
│   │   ├── agent_executor.py
│   │   ├── descriptions.txt
│   │   └── instructions.txt
│   └── alert/                           # Alert management agent (Port 8005)
│       ├── __main__.py
│       ├── agent.py
│       ├── agent_executor.py
│       ├── descriptions.txt
│       └── instructions.txt
│
├── mcp_servers/                         # MCP Server implementations
│   ├── searching/                       # Search MCP server (Port 9000)
│   │   ├── server.py                    # FastMCP server
│   │   └── utilities/
│   │       ├── parser.py                # Query parsing with OpenAI
│   │       ├── mdb_filter.py            # MongoDB filtering
│   │       └── reranker.py              # Hybrid reranking
│   ├── listings_mdb/                    # Listings MCP server (Port 9001)
│   │   ├── server.py                    # FastMCP server
│   │   └── utilities/
│   │       └── parser.py                # Listing parsing with OpenAI
│   └── alert_email/                     # Alert MCP server (Port 9002)
│       ├── server.py                    # FastMCP server
│       └── utilities/
│           ├── parser.py                # Alert message parsing
│           ├── email.py                 # SMTP email service
│           ├── listing_monitor.py       # Change stream monitor
│           └── alertHandler.py          # Alert CRUD operations
│
├── utilities/                           # Shared utilities
│   ├── a2a/                             # A2A protocol utilities
│   │   ├── agent_connect.py             # Agent connection client
│   │   ├── agent_discovery.py           # Agent registry discovery
│   │   └── agent_registry.json          # A2A agent URLs
│   ├── mcp/                             # MCP protocol utilities
│   │   ├── mcp_connect.py               # MCP connection manager
│   │   ├── mcp_discovery.py             # MCP server discovery
│   │   └── mcp_config.json              # MCP server configuration
│   └── common/
│       └── file_loader.py               # File loading utilities
│
├── db/                                  # Database connection
│   └── connection.py                    # MongoDB client singleton
│
├── app/                                 # CLI application
│   └── cmd/
│       └── cmd.py                       # Interactive CLI for testing
│
├── params.yaml                          # Reranker hyperparameters
├── pyproject.toml                       # Project metadata (uv)
├── requirements.txt                     # Python dependencies
├── .gitignore                           # Git ignore patterns
├── .python-version                      # Python version (3.12)
└── README.md                            # Project documentation
System Components
1. Orchestrator Agent (Host Agent)
Role: Central coordinator and intent classifier
Capabilities:

Analyzes user messages to determine intent (search/list/alert)
Routes requests to appropriate specialized agents
Handles ambiguous queries with clarifying questions
Maintains conversation context using Google ADK sessions

Decision Logic:
pythonIntent Detection:
- Keywords: "find", "search", "looking for" → Search Agent
- Keywords: "list my property", "create listing" → Listing Agent  
- Keywords: "alert me", "notify when" → Alert Agent
```

**Implementation Details**:
- Uses `_list_agents()` to discover available A2A agents from registry
- Uses `_delegate_task()` to forward requests with full context
- Implements `AgentExecutor` interface for A2A protocol compliance

### 2. Search Agent (Port 8003)
**Role**: Property discovery and matching

**Pipeline**:
1. **Message Parsing**: Extract location, price, bedrooms, amenities using OpenAI
2. **MongoDB Filtering**: Apply hard constraints (text search, price range)
3. **Hybrid Reranking**: Semantic similarity (0.6) + BM25 keyword matching (0.4)
4. **Result Formatting**: Top-K properties with relevance scores

**Example Query Processing**:
```
Input: "2BHK furnished near MIT under $2500"
↓
Parsed: {location: "MIT", price: 2500, rag_content: "2BHK furnished"}
↓
MongoDB: Text search on "MIT" + price <= 2500
↓
Retrieved: 47 candidates
↓
Reranked: Top 10 by hybrid scoring
```

**MCP Tools Used**:
- `search_properties(user_query, max_results)` - Full search pipeline
- `get_property_summary(user_query, max_results)` - Concise text summary
- `check_search_status()` - Health check

### 3. Listing Agent (Port 8004)
**Role**: Property listing creation and management

**Workflow**:
```
User Input (any format) 
    ↓
AI Parsing (GPT-4o-mini) → Structured JSON
    ↓
Validation (required fields check)
    ↓
Auto-Save to MongoDB
    ↓
Return Database ID + Confirmation
Features:

Accepts bullet points, paragraphs, or casual text
Extracts: address, price, bedrooms, bathrooms, amenities, rental terms
Handles updates via natural language ("change price to $3000")
Immediate database persistence (no confirmation loop)

MCP Tools Used:

parse_and_confirm_listing(raw_listing) - Parse unstructured text
update_listing_fields(parsed_json, changes) - Natural language updates
save_listing(parsed_json) - Persist to MongoDB
delete_listing(listing_id) - Remove listing

4. Alert Agent (Port 8005)
Role: Proactive property monitoring
Alert Matching Logic:
pythonMatch Conditions (AND):
1. Location: alert.location IN listing.address (case-insensitive)
2. Price: alert.max_price >= listing.price

Special Cases:
- alert.location = None → matches ANY location
- alert.max_price = None → matches ANY price
Real-Time Monitoring:

Uses MongoDB Change Streams (replica set required)
Watches tulire_listings collection for inserts
Processes matches and sends emails within 3 seconds
Background monitor: listing_monitor.py

MCP Tools Used:

create_alert(user_message) - Create alert from natural language
get_user_alerts(email) - List alerts for user
delete_alert(alert_id) - Remove alert
search_matching_listings(location, max_price) - Search current listings
check_listing_for_alerts(listing_id) - Manual alert check
get_all_alerts() - Admin statistics

Installation & Setup
Prerequisites
bash- Python 3.12
- MongoDB 4.0+ (configured as replica set)
- OpenAI API key
- SMTP server credentials (Gmail recommended)
- uv package manager (optional but recommended)
1. MongoDB Replica Set Setup
bash# Add to mongod.conf
replication:
  replSetName: "rs0"

# Restart MongoDB and initialize
mongosh --eval "rs.initiate()"
2. Environment Configuration
bash# Create .env file in project root
MONGODB_URL_KEY=mongodb://localhost:27017
OPENAI_API_KEY=your_openai_api_key
SENDER_EMAIL=your_email@gmail.com
EMAIL_APP_PASSWORD=your_gmail_app_password
3. Install Dependencies
bash# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
Key Packages:

a2a-sdk>=0.3.10 - Agent-to-agent protocol
fastmcp>=2.13.0 - MCP server framework
google-adk>=1.18.0 - Google Agent Development Kit
langchain>=1.0.3 - LLM orchestration
pymongo>=4.15.3 - MongoDB driver
sentence-transformers>=5.1.2 - Semantic embeddings

4. Start MCP Servers
bash# Terminal 1 - Search MCP Server (Port 9000)
uv run python -m mcp_servers.searching.server

# Terminal 2 - Listings MCP Server (Port 9001)
uv run python -m mcp_servers.listings_mdb.server 

# Terminal 3 - Alert MCP Server (Port 9002)
uv run python -m mcp_servers.alert_email.server

# Terminal 4 - Change Stream Monitor (Real-time alerts)
uv run python -m mcp_servers.alert_email.utilities.listing_monitor
5. Start A2A Agents
bash# Terminal 5 - Host Agent/Orchestrator (Port 8001)
uv run python -m agents.host

# Terminal 6 - Search Agent (Port 8003)
uv run python -m agents.search

# Terminal 7 - Listings Agent (Port 8004)
uv run python -m agents.listings

# Terminal 8 - Alert Agent (Port 8005)
uv run python -m agents.alert
6. Test the System
bash# Interactive CLI
uv run python -m app.cmd.cmd --agent http://localhost:8001
```

## Usage Examples

### Example 1: Property Search
```
User: "Find 2BHK apartments in Jersey City under $2000"

Orchestrator: [Detects search intent → Routes to Search Agent]

Search Agent Response:
Found 8 properties matching your criteria! Here are the top 5:

1. **2BHK Furnished Apartment**
   - Rent: $1,800/month
   - Location: 123 Main St, Jersey City, NJ
   - Bedrooms: 2 | Bathrooms: 2
   - Amenities: Furnished, Parking, 24/7 Water
   
2. **2BHK Semi-Furnished Flat**
   - Rent: $1,950/month
   - Location: 456 Oak Ave, Jersey City, NJ
   - Bedrooms: 2 | Bathrooms: 1
   - Amenities: Semi-Furnished, Lift
   ...
```

### Example 2: Create Listing
```
User: "I want to list my 3BHK flat in Greater Noida near Galgotias, 
      fully furnished, 27k rent"

Orchestrator: [Detects listing intent → Routes to Listing Agent]

Listing Agent Response:
Listing uploaded! Here's what I've saved:

**Property Listing Summary**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Address**: Greater Noida near Galgotias University
**Monthly Rent**: $27,000
**Bedrooms**: 3
**Bathrooms**: Not specified
**Amenities**: Fully furnished

**Database ID**: 6919d7f2e2b5cf361a727f14

Your property is now live!
```

### Example 3: Set Up Alerts
```
User: "Alert me for properties in Brooklyn under $2500 at john@email.com"

Orchestrator: [Detects alert intent → Routes to Alert Agent]

Alert Agent Response:
Alert Created Successfully!

**Alert ID**: 673d8f2a4b5c1a2d3e4f5678
**Email**: john@email.com
**Location**: Brooklyn
**Max Price**: $2,500

You'll receive notifications when new properties matching 
your criteria are listed.

[When new matching listing appears]
→ Email sent within 3 seconds with full property details
Orchestrator Decision Matrix
User QueryDetected IntentRouted ToReasoning"Show me 2BHK apartments"SearchSearch AgentDiscovery keywords"I want to rent out my house"ListingListing AgentOwnership indicators"Notify me about new properties"AlertAlert AgentFuture monitoring"What can you do?"ClarificationOrchestratorAmbiguous intent
Agent Communication Protocol
MCP Message Format
json{
  "tool_name": "search_properties",
  "arguments": {
    "user_query": "Find 2BHK in Brooklyn under $2500",
    "max_results": 10
  }
}
A2A Message Format
json{
  "message": {
    "role": "user",
    "messageId": "uuid-v4",
    "parts": [
      {
        "text": "Find 2BHK apartments",
        "kind": "text"
      }
    ]
  }
}
A2A Response Format
json{
  "result": {
    "status": {
      "message": {
        "parts": [
          {
            "text": "Found 8 matching properties...",
            "kind": "text"
          }
        ]
      }
    }
  }
}
Database Schema
Collections
tulire_listings
javascript{
  _id: ObjectId,
  address: String,                    // Full street address (required)
  price: Number,                      // Monthly rent in dollars (required)
  bedroom: Number,                    // Number of bedrooms (required)
  bathroom: Number,                   // Number of bathrooms
  description: String,                // Property description (required)
  amenities: {
    appliances: [String],            // e.g., ["Refrigerator", "Microwave"]
    utilities_included: [String],    // e.g., ["Water", "Electricity"]
    other_amenities: [String]        // e.g., ["Parking", "Gym"]
  },
  rental_terms: {
    application_fee: String,
    security_deposit: String,
    lease_terms: String,
    availability: String
  },
  pet_friendly: String,              // "yes", "no", or empty
  listing_url: String,
  contact: String,
  source: String,                    // "user_created" or "tulire_realty"
  last_updated: String               // ISO date string
}
alert_mongodb
javascript{
  _id: ObjectId,
  email: String,                     // User email (required, lowercase)
  location: String,                  // Nullable - city/neighborhood
  price: Number,                     // Nullable - max budget
  status: String,                    // "active" or "inactive"
  created_at: Date,
  updated_at: Date,
  original_message: String           // Raw user input
}
Indexes
tulire_listings:

Text index on ["address", "title"] for location search
Numeric index on rent_price for price filtering

alert_mongodb:

Index on email for user lookups
Index on location for location-based queries
Compound index on [("email", 1), ("location", 1)]

User Personas
1. Students (Search Agent)
Need: Find affordable housing near campus
Workflow: Natural language search → Filtered results → Direct contact
Example: "Find 2BHK near MIT under $2000 with parking"
2. Landlords (Listing Agent)
Need: Quickly list properties without complex forms
Workflow: Casual description → Auto-parsed listing → Instant publication
Example: "3BHK flat in Greater Noida, 27k rent, fully furnished"
3. Proactive Renters (Alert Agent)
Need: Be first to know about new listings
Workflow: Set criteria → Automatic monitoring → Email notifications
Example: "Alert me for properties in Brooklyn under $2500"
Security & Privacy

Email addresses stored in lowercase, trimmed format
No password storage (email-only identification)
Secure SMTP with TLS encryption
MongoDB connection with authentication
Environment variables for sensitive credentials
No API keys exposed in code

Configuration Files
params.yaml - Reranker Hyperparameters
yamlprimary_ranker:
  alpha: 0.6  # Semantic similarity weight
  beta: 0.4   # BM25 keyword weight
utilities/a2a/agent_registry.json - A2A Agents
json[
    "http://localhost:8003",  // Search Agent
    "http://localhost:8004",  // Listing Agent
    "http://localhost:8005"   // Alert Agent
]
utilities/mcp/mcp_config.json - MCP Servers
json{
    "mcpServers": {
        "property_search": {
            "command": "streamable_http",
            "args": ["http://localhost:9000/mcp"]
        },
        "listings_mongodb": {
            "command": "streamable_http", 
            "args": ["http://localhost:9001/mcp"]
        },
        "alert_service": {
            "command": "streamable_http", 
            "args": ["http://localhost:9002/mcp"]
        }
    }
}
