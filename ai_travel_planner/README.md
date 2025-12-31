# AI Travel Planner 🌍✈️

An intelligent travel planning application that uses AI (LangChain + GPT-4) to generate personalized, day-by-day travel itineraries with real-time weather data, cost estimation, and local experiences.

## 🚀 Features

- **AI-Powered Itinerary Generation**: Creates detailed, day-by-day travel plans using GPT-4
- **Personalization**: Customized based on travel style, budget, interests, and dietary restrictions
- **Real-Time Weather Integration**: Incorporates weather forecasts into planning
- **Cost Estimation**: Detailed budget breakdown for accommodation, food, activities, and transport
- **Local Experiences**: Curated hidden gems and authentic local recommendations
- **Interactive Modifications**: Chat-based refinement and day-specific regeneration
- **Multi-Version Support**: Save and compare different itinerary versions
- **Export & Share**: PDF export and shareable itinerary links

## 🛠️ Tech Stack

- **Backend**: Django 5.0, Python 3.10+
- **AI/ML**: LangChain, OpenAI GPT-4
- **Vector Store**: ChromaDB
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL (SQLite for development)
- **External APIs**:
  - OpenWeatherMap (Weather data)
  - Google Maps API (Places, geocoding)
  - ExchangeRate API (Currency conversion)

## 📋 Prerequisites

- Python 3.10 or higher
- PostgreSQL (or SQLite for development)
- Redis (for Celery)
- API Keys:
  - OpenAI API Key
  - Google Maps API Key
  - OpenWeatherMap API Key
  - Currency API Key (optional)

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-travel-planner.git
cd ai-travel-planner
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (use SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3
# Or PostgreSQL for production:
# DATABASE_URL=postgresql://user:password@localhost:5432/ai_travel_planner

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
OPENAI_API_KEY=your-openai-api-key
GOOGLE_MAPS_API_KEY=your-google-maps-key
WEATHER_API_KEY=your-openweather-key
CURRENCY_API_KEY=your-currency-api-key
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## 🏃 Running the Application

### Start Redis (Required for Celery)

```bash
redis-server
```

### Start Celery Worker (In a separate terminal)

```bash
celery -A ai_travel_planner worker --loglevel=info
```

### Start Celery Beat (Optional, for scheduled tasks)

```bash
celery -A ai_travel_planner beat --loglevel=info
```

### Start Django Development Server

```bash
python manage.py runserver
```

Visit: `http://localhost:8000`

## 📝 Usage

### 1. Plan a Trip

1. Navigate to `/trips/plan/`
2. Fill in the trip details:
   - Destination
   - Travel dates
   - Budget
   - Travel style (Adventure, Relaxation, Cultural, etc.)
   - Group size
   - Interests and dietary restrictions

3. Submit the form
4. Wait for AI to generate your itinerary (1-3 minutes)

### 2. View Itinerary

- See day-by-day breakdown with activities, costs, and timings
- View local experiences and hidden gems
- Check weather forecast
- See estimated budget breakdown

### 3. Refine Itinerary

- Use chat interface to make conversational changes
- Regenerate specific days
- Add or remove activities
- Adjust budget allocation

### 4. Save & Share

- Save itinerary to your account
- Export as PDF
- Generate shareable link
- Compare different versions

## 🗂️ Project Structure

```
ai_travel_planner/
│
├── ai_travel_planner/          # Main project directory
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
│
├── apps/
│   ├── core/                   # Core app (home, about, etc.)
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── templates/
│   │   │   └── core/
│   │   │       ├── base.html
│   │   │       ├── home.html
│   │   │       └── about.html
│   │   └── static/
│   │       └── core/
│   │           ├── css/
│   │           ├── js/
│   │           └── images/
│   │
│   ├── trips/                  # Trip planning app
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── serializers.py
│   │   ├── tasks.py            # Celery tasks
│   │   ├── templates/
│   │   │   └── trips/
│   │   │       ├── plan_trip.html
│   │   │       ├── itinerary_detail.html
│   │   │       ├── my_trips.html
│   │   │       └── partials/
│   │   └── static/
│   │       └── trips/
│   │
│   ├── ai_engine/              # AI/LangChain logic
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── chains.py           # LangChain chains
│   │   ├── prompts.py          # Prompt templates
│   │   ├── agents.py           # LangChain agents
│   │   ├── vector_store.py     # ChromaDB integration
│   │   ├── parsers.py          # Output parsers
│   │   └── utils.py
│   │
│   ├── external_apis/          # External API integrations
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── weather.py          # Weather API client
│   │   ├── maps.py             # Google Maps client
│   │   ├── currency.py         # Currency API client
│   │   └── utils.py
│   │
│   └── users/                  # User management
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       ├── forms.py
│       ├── templates/
│       │   └── users/
│       │       ├── login.html
│       │       ├── register.html
│       │       ├── profile.html
│       │       └── dashboard.html
│       └── static/
│           └── users/
│
├── templates/                  # Global templates
│   └── base.html
│
├── static/                     # Global static files
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/                      # User uploaded files
│
├── chroma_db/                  # ChromaDB persistence
│
├── logs/                       # Application logs
│
├── manage.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml          # Optional: for Docker setup
```