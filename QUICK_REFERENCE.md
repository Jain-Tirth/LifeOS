# Save to Agent - Quick Reference Card

## REST API Endpoints

### Direct Model Endpoints
```
POST /api/meal-plans/           - Save meal plan
POST /api/tasks/                - Save task  
POST /api/study-sessions/       - Save study session
POST /api/wellness-activities/  - Save wellness activity
```

### Generic Save (Auto-routes to correct model)
```
POST /api/save-agent-response/
Body: {
  "agent_type": "meal_planner_agent|productivity_agent|study_agent|wellness_agent",
  "session_id": "uuid-string",
  "data": { ...model-specific-fields... }
}
```

### Bulk Save
```
POST /api/bulk-save-agent-responses/
Body: {
  "items": [
    {"agent_type": "...", "session_id": "...", "data": {...}},
    {...}
  ]
}
```

### Get Saved Items
```
GET /api/sessions/{session_id}/saved-items/
Returns: All items saved in that session
```

## Python Helper Functions

```python
from agents.services.save_helper import (
    save_meal_plan,
    save_task,
    save_study_session,
    save_wellness_activity,
    save_agent_output,      # Auto-routes by agent_type
    bulk_save_outputs
)

# Example: Save a task
task = save_task(
    data={'title': 'My Task', 'priority': 'high'},
    session_id='uuid-string',  # or session=session_obj
    user=user                   # Optional
)

# Example: Auto-route by agent type
item = save_agent_output(
    agent_type='meal_planner_agent',
    data={...},
    session_id='uuid-string'
)

# Example: Bulk save
result = bulk_save_outputs(
    items=[...],
    default_session=session
)
```

## Request Body Examples

### Meal Plan
```json
{
  "date": "2026-02-17",
  "meal_type": "dinner",
  "meal_name": "Grilled Salmon",
  "ingredients": ["salmon", "lemon"],
  "instructions": "Grill for 15 minutes",
  "session_id": "uuid-string"
}
```

### Task
```json
{
  "title": "Complete report",
  "description": "Q1 report",
  "priority": "high",
  "status": "todo",
  "due_date": "2026-02-20T15:00:00Z",
  "session_id": "uuid-string"
}
```

### Study Session
```json
{
  "subject": "Python",
  "topic": "Decorators",
  "duration": 60,
  "notes": "Covered advanced topics",
  "session_id": "uuid-string"
}
```

### Wellness Activity
```json
{
  "activity_type": "exercise",
  "duration": 30,
  "intensity": "moderate",
  "notes": "Morning run",
  "recorded_at": "2026-02-17T08:00:00Z",
  "session_id": "uuid-string"
}
```

## Response Format

### Success
```json
{
  "success": true,
  "message": "Item saved successfully",
  "data": { ...saved-object... }
}
```

### Error
```json
{
  "success": false,
  "errors": {
    "field_name": ["Error message"]
  }
}
```

## Query Parameters

All list endpoints support:
- `session_id` - Filter by session
- Model-specific filters:
  - Meal Plans: `date`, `meal_type`
  - Tasks: `status`, `priority`
  - Study Sessions: `subject`
  - Wellness: `activity_type`, `start_date`, `end_date`

Example:
```
GET /api/tasks/?session_id=uuid-string&status=todo&priority=high
```

## Quick Test

```bash
# Test meal plan save
curl -X POST http://localhost:8000/api/meal-plans/ \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-02-17","meal_type":"dinner","meal_name":"Test"}'

# Test generic save
curl -X POST http://localhost:8000/api/save-agent-response/ \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"productivity_agent","data":{"title":"Test Task"}}'
```

## Frontend Usage (JavaScript)

```javascript
// Using existing functions from api/chat.js
import { saveMealPlan, saveTask } from '../../api/chat';

// Save from agent response
const result = await saveMealPlan({
  date: '2026-02-17',
  meal_type: 'dinner',
  meal_name: 'Agent Generated Meal',
  instructions: agentResponse,
  session_id: currentSessionId
});

if (result.success) {
  console.log('Saved!', result.data);
}
```

## Agent Types

- `meal_planner_agent` → MealPlan
- `productivity_agent` → Task
- `study_agent` → StudySession
- `wellness_agent` → WellnessActivity

Keywords also work:
- "meal", "planner" → MealPlan
- "productivity", "task" → Task
- "study", "buddy" → StudySession
- "wellness" → WellnessActivity
