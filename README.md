# ShopStream Reactive Commerce Advisor

A reactive commerce advisor that observes inventory changes and velocity spikes, triggers a background recommendation pipeline, and queues suggestions for merchandising approval.

## Features

- Real-time inventory monitoring and reactive suggestions
- Pluggable strategy pattern (Rule-based vs AI-powered)
- SQLite with WAL mode for concurrent read/write operations
- Background processing with asyncio queue worker
- RESTful API for product management and suggestion resolution

## Tech Stack

- **Python 3.11+**
- **FastAPI** - High-performance web framework
- **SQLAlchemy 2.0 Async** - Async ORM for database operations
- **SQLite with WAL Mode** - Lightweight database with concurrency support
- **Pydantic v2** - Data validation and serialization

## Project Structure

```
shopstream/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, lifespan worker startup, CORS
│   ├── config.py               # Env settings, default strategy toggle
│   ├── database.py             # SQLite async engine with WAL mode pragma, sessionmaker
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py            # ProductCategory, ProductStatus, SuggestionStatus, TriggerReason, PriceDirection
│   │   ├── product.py          # Product model (with Sprint 2 nullable fields: cost_price, supplier_id, competitor_price)
│   │   ├── pricing_suggestion.py # PricingSuggestion model with compound uniqueness constraint
│   │   └── reorder_suggestion.py # ReorderSuggestion model with compound uniqueness constraint
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── product.py          # Create/Read schemas for Product
│   │   └── suggestion.py       # Read & Resolution schemas for suggestions
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── base.py             # ABC CommerceAdvisorStrategy and Recommendation dataclasses
│   │   ├── rule_based.py       # Deterministic math baseline
│   │   ├── ai_advisor.py       # Structured prompt, timeout race, bounds validation, fallback
│   │   ├── llm_gateway.py      # Async HTTP client calling Groq or Ollama based on env
│   │   └── manager.py          # StrategyManager holding active strategy singleton
│   ├── queue/
│   │   ├── __init__.py
│   │   ├── bus.py              # Global asyncio.Queue instance
│   │   └── worker.py           # Background loop: pop item -> check triggers -> check dupes -> run strategy -> persist suggestions
│   └── routers/
│       ├── __init__.py
│       ├── products.py         # POST /products, GET /products, PATCH /products/{id}/stock, POST /products/{id}/orders, on-demand suggests
│       └── suggestions.py      # PATCH /pricing-suggestions/{id}, PATCH /reorder-suggestions/{id} (updates Product on ACCEPT)
├── seed.py                     # Populates DB with 8 initial products (including 1 near low-stock threshold)
├── requirements.txt            # All required pinned dependencies
└── README.md                   # Setup instructions and run commands
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd shopstream
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (optional):**
   Create a `.env` file in the project root:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./shopstream.db
   AI_MODEL=gemini-pro
   GOOGLE_API_KEY=your-google-api-key-here
   DEFAULT_STRATEGY=RULE_BASED
   ```

5. **Seed the database with initial products:**
   ```bash
   python seed.py
   ```

6. **Run the application:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### Products
- `POST /api/v1/products` - Create a new product
- `GET /api/v1/products` - List all products
- `GET /api/v1/products/{id}` - Get a specific product
- `PATCH /api/v1/products/{id}` - Update a product
- `PATCH /api/v1/products/{id}/stock` - Update product stock level
- `POST /api/v1/products/{id}/orders` - Record an order/sale

### Suggestions
- `GET /api/v1/pricing-suggestions` - List pricing suggestions
- `GET /api/v1/reorder-suggestions` - List reorder suggestions
- `PATCH /api/v1/pricing-suggestions/{id}` - Update pricing suggestion status
- `PATCH /api/v1/reorder-suggestions/{id}` - Update reorder suggestion status

## Strategies

The system supports two strategies for generating recommendations:

1. **Rule-Based Strategy (`RULE_BASED`)**
   - Increases prices by 10% for low stock items
   - Increases prices by 5% for velocity spikes
   - Recommends reorder quantities based on buffer calculations

2. **AI Advisor Strategy (`AI_ADVISOR`)**
   - Uses Google's Gemini LLM to generate context-aware recommendations
   - Includes 4.5s timeout with fallback to rule-based strategy
   - Structured prompts with bounds validation

## Database

The application uses SQLite with WAL mode enabled for better concurrency handling. The database file is created automatically as `shopstream.db` in the project root directory.

## Development

To run the development server with auto-reload:
```bash
uvicorn app.main:app --reload
```

The API documentation will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
