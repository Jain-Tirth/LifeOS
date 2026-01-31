# LifeOS - Personal Life Management System

A Django-based personal life management system powered by AI agents to help manage meals, productivity, study, and wellness.

## Features

- **Meal Planner Agent**: AI-powered meal planning based on preferences
- **Productivity Agent**: Task management and productivity tracking
- **Study Buddy**: Learning assistance and study session tracking
- **Wellness Agent**: Health and wellness activity monitoring

## Project Structure

```
LifeOS/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── lifeos/                   # Django project settings
│   ├── __init__.py
│   ├── settings.py           # Project configuration
│   ├── urls.py               # Main URL routing
│   ├── wsgi.py               # WSGI application
│   └── asgi.py               # ASGI application
├── agents/                   # Agents Django app
│   ├── models.py             # Database models
│   ├── views.py              # View logic
│   ├── urls.py               # Agent URLs
│   ├── admin.py              # Admin interface
│   └── services/             # Agent implementations
│       ├── meal_planner.py
│       ├── orchestrator.py
│       └── __init__.py
├── api/                      # REST API app
│   ├── views.py              # API endpoints
│   ├── serializers.py        # Data serialization
│   └── urls.py               # API routing
├── client/                   # Frontend (to be implemented)

```

## Setup Instructions

### 1. Create a virtual environment

```bash
python -m venv venv
```

### 2. Activate the virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the project root:

```env
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key-here
```

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to see your application.

## API Endpoints

### Agent Sessions
- `POST /api/create-session/` - Create new agent session
- `GET /api/sessions/` - List all sessions
- `POST /api/sessions/{id}/send_message/` - Send message to agent

### Meal Plans
- `GET /api/meal-plans/` - List meal plans
- `POST /api/meal-plans/` - Create meal plan
- `GET /api/meal-plans/{id}/` - Get specific meal plan

### Tasks
- `GET /api/tasks/` - List tasks
- `POST /api/tasks/` - Create task
- `GET /api/tasks/{id}/` - Get specific task

### Study Sessions
- `GET /api/study-sessions/` - List study sessions
- `POST /api/study-sessions/` - Create study session

### Wellness Activities
- `GET /api/wellness-activities/` - List wellness activities
- `POST /api/wellness-activities/` - Log wellness activity

## Admin Panel

Access the Django admin at `http://localhost:8000/admin/` with your superuser credentials.

## Development

- Models are defined in `agents/models.py`
- API views are in `api/views.py`
- Agent logic is in `agents/services/`
- URL routing in respective `urls.py` files

## Next Steps

1. Migrate remaining agent implementations from `server/agents/`
2. Implement frontend in the `client/` directory
3. Add authentication and user management
4. Enhance agent capabilities
5. Add WebSocket support for real-time agent interactions

## License

MIT License
