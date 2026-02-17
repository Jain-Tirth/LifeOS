# Save to Agent Backend - Implementation Documentation

## Overview

The save-to-agent backend logic has been implemented to allow agent responses to be persisted to the database. This includes meal plans, tasks, study sessions, and wellness activities.

## Key Features

1. **Automatic session_id to session object conversion**: Serializers handle UUID string session_ids
2. **User assignment**: Automatically assigns authenticated users to saved items
3. **Flexible saving**: Multiple endpoints for different use cases
4. **Validation and error handling**: Comprehensive error messages
5. **Permission support**: Works with both authenticated and anonymous users
6. **Agent helper module**: Programmatic API for agents to save data

## API Endpoints

### 1. Model-Specific Endpoints (ViewSets)

These are standard REST endpoints for each model:

#### Meal Plans
- **POST** `/api/meal-plans/` - Create a meal plan
- **GET** `/api/meal-plans/` - List meal plans (filtered by user)
- **GET** `/api/meal-plans/{id}/` - Get specific meal plan
- **PUT/PATCH** `/api/meal-plans/{id}/` - Update meal plan
- **DELETE** `/api/meal-plans/{id}/` - Delete meal plan

Query parameters: `date`, `meal_type`, `session_id`

#### Tasks
- **POST** `/api/tasks/` - Create a task
- **GET** `/api/tasks/` - List tasks (filtered by user)
- **GET** `/api/tasks/{id}/` - Get specific task
- **PUT/PATCH** `/api/tasks/{id}/` - Update task
- **DELETE** `/api/tasks/{id}/` - Delete task

Query parameters: `status`, `priority`, `session_id`

#### Study Sessions
- **POST** `/api/study-sessions/` - Create a study session
- **GET** `/api/study-sessions/` - List study sessions (filtered by user)
- **GET** `/api/study-sessions/{id}/` - Get specific study session
- **PUT/PATCH** `/api/study-sessions/{id}/` - Update study session
- **DELETE** `/api/study-sessions/{id}/` - Delete study session

Query parameters: `subject`, `session_id`

#### Wellness Activities
- **POST** `/api/wellness-activities/` - Create a wellness activity
- **GET** `/api/wellness-activities/` - List wellness activities (filtered by user)
- **GET** `/api/wellness-activities/{id}/` - Get specific wellness activity
- **PUT/PATCH** `/api/wellness-activities/{id}/` - Update wellness activity
- **DELETE** `/api/wellness-activities/{id}/` - Delete wellness activity

Query parameters: `activity_type`, `session_id`, `start_date`, `end_date`

### 2. Orchestrator Endpoints

#### Save Agent Response
**POST** `/api/save-agent-response/`

Generic endpoint that routes to the correct model based on agent type.

**Request:**
```json
{
  "agent_type": "meal_planner_agent",
  "session_id": "uuid-string",
  "data": {
    "date": "2026-02-17",
    "meal_type": "dinner",
    "meal_name": "Grilled Salmon",
    "ingredients": ["salmon", "lemon", "herbs"],
    "instructions": "Grill for 15 minutes..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Agent response saved successfully",
  "data": {
    "id": 1,
    "meal_name": "Grilled Salmon",
    ...
  }
}
```

#### Bulk Save Agent Responses
**POST** `/api/bulk-save-agent-responses/`

Save multiple items at once.

**Request:**
```json
{
  "items": [
    {
      "agent_type": "productivity_agent",
      "session_id": "uuid-string",
      "data": {
        "title": "Complete project",
        "priority": "high"
      }
    },
    {
      "agent_type": "wellness_agent",
      "session_id": "uuid-string",
      "data": {
        "activity_type": "exercise",
        "duration": 30,
        "recorded_at": "2026-02-17T10:00:00Z"
      }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "saved_count": 2,
  "error_count": 0,
  "saved_items": [...],
  "errors": []
}
```

#### Get Session Saved Items
**GET** `/api/sessions/{session_id}/saved-items/`

Retrieve all items saved from a specific session.

**Response:**
```json
{
  "session_id": "uuid-string",
  "saved_items": {
    "meal_plans": [...],
    "tasks": [...],
    "study_sessions": [...],
    "wellness_activities": [...]
  },
  "total_count": 5
}
```

## Data Models

### MealPlan
```python
{
  "date": "2026-02-17",  # Required
  "meal_type": "breakfast|lunch|dinner|snack",  # Required
  "meal_name": "String",  # Required
  "ingredients": {},  # Optional JSON
  "instructions": "String",  # Optional
  "nutritional_info": {},  # Optional JSON
  "preferences": {},  # Optional JSON
  "session_id": "uuid-string"  # Optional
}
```

### Task
```python
{
  "title": "String",  # Required
  "description": "String",  # Optional
  "priority": "low|medium|high|urgent",  # Optional, default: medium
  "status": "todo|in_progress|completed|cancelled",  # Optional, default: todo
  "due_date": "2026-02-20T15:00:00Z",  # Optional
  "session_id": "uuid-string"  # Optional
}
```

### StudySession
```python
{
  "subject": "String",  # Required
  "topic": "String",  # Optional
  "duration": 60,  # Required (minutes)
  "notes": "String",  # Optional
  "resources": {},  # Optional JSON
  "session_id": "uuid-string"  # Optional
}
```

### WellnessActivity
```python
{
  "activity_type": "exercise|meditation|sleep|hydration|mood",  # Required
  "duration": 30,  # Optional (minutes)
  "intensity": "String",  # Optional
  "notes": "String",  # Optional
  "metadata": {},  # Optional JSON
  "recorded_at": "2026-02-17T10:00:00Z",  # Required
  "session_id": "uuid-string"  # Optional
}
```

## Python Agent Helper

Agents can use the `save_helper` module to programmatically save data:

```python
from agents.services.save_helper import (
    save_meal_plan,
    save_task,
    save_study_session,
    save_wellness_activity,
    save_agent_output,  # Auto-routes based on agent type
    bulk_save_outputs
)

# Example: Save a meal plan
meal_plan = save_meal_plan(
    data={
        'date': '2026-02-17',
        'meal_type': 'dinner',
        'meal_name': 'Pasta Primavera',
        'instructions': 'Cook pasta...'
    },
    session_id='your-session-uuid',
    user=request.user  # Optional
)

# Example: Auto-route based on agent type
saved_item = save_agent_output(
    agent_type='productivity_agent',
    data={'title': 'New Task', 'priority': 'high'},
    session_id='your-session-uuid'
)

# Example: Bulk save
result = bulk_save_outputs(
    items=[
        {
            'agent_type': 'meal_planner_agent',
            'data': {...}
        },
        {
            'agent_type': 'productivity_agent',
            'data': {...}
        }
    ],
    default_user=request.user
)
```

## Frontend Integration

The frontend can use the existing API calls:

```javascript
// From frontend/src/api/chat.js
import { saveMealPlan, saveTask, saveStudySession, saveWellnessActivity } from '../../api/chat';

// Save meal plan
const result = await saveMealPlan({
  date: '2026-02-17',
  meal_type: 'dinner',
  meal_name: 'Grilled Chicken',
  instructions: 'Season and grill...',
  session_id: sessionId  // This will be converted to session object
});

// Save task
const result = await saveTask({
  title: 'Complete report',
  description: 'Finish Q1 report',
  priority: 'high',
  status: 'todo',
  session_id: sessionId
});
```

Or use the new generic endpoint:

```javascript
// Generic save endpoint
const response = await fetch('/api/save-agent-response/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agent_type: 'meal_planner_agent',
    session_id: sessionId,
    data: {
      date: '2026-02-17',
      meal_type: 'dinner',
      meal_name: 'Pasta',
      instructions: 'Cook...'
    }
  })
});
```

## Features

### Session Linking
All saved items can be linked to an agent session by providing `session_id`:
- Frontend passes the UUID string
- Backend automatically converts to AgentSession object
- Validation ensures session exists
- Items can be queried by session later

### User Association
- Authenticated users: Items automatically assigned to current user
- Anonymous users: Items saved without user assignment
- Users only see their own items in list views

### Filtering
All endpoints support filtering:
- By user (automatic)
- By session_id
- By type-specific fields (status, priority, date, etc.)

### Error Handling
Comprehensive error responses:
```json
{
  "success": false,
  "errors": {
    "field_name": ["Error message"]
  }
}
```

## Testing

Test the endpoints using curl or Postman:

```bash
# Save a meal plan
curl -X POST http://localhost:8000/api/meal-plans/ \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-02-17",
    "meal_type": "dinner",
    "meal_name": "Test Meal",
    "session_id": "your-session-uuid"
  }'

# Get saved items for a session
curl http://localhost:8000/api/sessions/your-session-uuid/saved-items/

# Use generic save endpoint
curl -X POST http://localhost:8000/api/save-agent-response/ \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "productivity_agent",
    "session_id": "your-session-uuid",
    "data": {
      "title": "Test Task",
      "priority": "high"
    }
  }'
```

## Summary

The save-to-agent backend is fully implemented with:

✅ All model serializers with session_id support
✅ Enhanced ViewSets with validation and filtering
✅ Generic save endpoint for agent responses
✅ Bulk save endpoint for multiple items
✅ Session saved items retrieval endpoint
✅ Python helper module for programmatic saves
✅ Comprehensive error handling
✅ User and permission support
✅ Frontend-ready API

The frontend team can now integrate these endpoints to save agent responses from the UI.
