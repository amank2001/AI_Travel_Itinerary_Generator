# Quick Start Guide - AI Travel Planner

Get up and running in 10 minutes!

## Prerequisites
- Python 3.10+
- pip
- Git

## Step 1: Clone & Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/yourusername/ai-travel-planner.git
cd ai-travel-planner

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Environment (3 minutes)

```bash
# Copy environment template
cp .env.example .env
```

**Edit `.env` file with your API keys:**

```env
SECRET_KEY=django-insecure-your-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Use SQLite for quick start
DATABASE_URL=sqlite:///db.sqlite3

# Redis (install locally or use default)
REDIS_URL=redis://localhost:6379/0

# Required: Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-key-here

# Optional but recommended:
GOOGLE_MAPS_API_KEY=your-google-maps-key
WEATHER_API_KEY=your-openweather-key
CURRENCY_API_KEY=your-currency-api-key
```

### How to Get API Keys:

1. **OpenAI** (Required): https://platform.openai.com/api-keys
2. **Google Maps** (Optional): https://console.cloud.google.com/
3. **OpenWeather** (Optional): https://openweathermap.org/api
4. **Currency API** (Optional): https://exchangerate-api.com/

## Step 3: Initialize Database (2 minutes)

```bash
# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
# Enter username, email, and password when prompted

# Create static files directory
mkdir -p static logs
```

## Step 4: Start Services (3 minutes)

### Terminal 1 - Start Redis (if installed locally)
```bash
redis-server
```
*Or skip if using Docker: `docker run -d -p 6379:6379 redis`*

### Terminal 2 - Start Celery Worker
```bash
celery -A ai_travel_planner worker --loglevel=info
```

### Terminal 3 - Start Django Server
```bash
python manage.py runserver
```

## Step 5: Test the Application

1. **Open browser**: http://localhost:8000
2. **Login**: Use the superuser credentials you created
3. **Plan a trip**: 
   - Go to `/trips/plan/`
   - Fill in trip details (e.g., "Paris, France", 5 days, $2000)
   - Submit and wait 2-3 minutes for AI generation

## Troubleshooting

### Redis Connection Error
```bash
# Install Redis
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# Download from: https://github.com/microsoftarchive/redis/releases
```

### Celery Not Processing
```bash
# Check Redis is running
redis-cli ping  # Should return "PONG"

# Restart Celery worker with debug
celery -A ai_travel_planner worker --loglevel=debug
```

### OpenAI API Error
- Verify API key is correct in `.env`
- Check you have credits: https://platform.openai.com/account/usage
- Test key: 
```python
import openai
openai.api_key = "your-key"
openai.models.list()
```

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python version
python --version  # Should be 3.10+
```

## Next Steps

### Customize Your Installation

1. **Change Travel Styles**: Edit `apps/trips/models.py`
2. **Modify AI Prompts**: Edit `apps/ai_engine/prompts.py`
3. **Adjust LLM Model**: Edit `apps/ai_engine/chains.py`
4. **Add Custom Features**: See full README.md

### Production Deployment

```bash
# Switch to PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Disable debug mode
DEBUG=False

# Set proper secret key
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Collect static files
python manage.py collectstatic

# Run with Gunicorn
gunicorn ai_travel_planner.wsgi:application
```

## Minimal Working Example

If you just want to test without external APIs:

```env
# .env minimal configuration
SECRET_KEY=test-key-for-development
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-openai-key

# Leave others empty - app will use fallbacks
GOOGLE_MAPS_API_KEY=
WEATHER_API_KEY=
CURRENCY_API_KEY=
```

The application will work with:
- ✅ AI itinerary generation (OpenAI only)
- ⚠️ Default weather data (if no Weather API)
- ⚠️ Limited location data (if no Maps API)
- ⚠️ Basic currency conversion (if no Currency API)

## Common Commands

```bash
# Create new app
python manage.py startapp app_name

# Make migrations after model changes
python manage.py makemigrations
python manage.py migrate

# Access Django shell
python manage.py shell

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Check for issues
python manage.py check

# View Celery tasks
celery -A ai_travel_planner inspect active
```

## Support

- 📖 Full documentation: See README.md
- 🐛 Issues: https://github.com/yourusername/ai-travel-planner/issues
- 💬 Discussions: https://github.com/yourusername/ai-travel-planner/discussions

**Ready to travel! 🚀**