from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with email and password"""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as the primary identifier"""
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the full name of the user"""
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def get_short_name(self):
        """Return the short name of the user"""
        return self.first_name or self.email


class UserProfile(models.Model):
    """
    Persistent user preferences that ALL agents can access.
    This is the 'memory' that makes LifeOS actually personal.
    Auto-created when a user registers.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Temporal
    timezone = models.CharField(
        max_length=50, default='Asia/Kolkata',
        help_text="User's timezone for scheduling and reminders"
    )
    
    # Dietary (Meal Planner Agent)
    dietary_preferences = models.JSONField(
        default=dict, blank=True,
        help_text="e.g. {'type': 'vegetarian', 'allergies': ['nuts'], 'cuisine': ['Indian', 'Italian']}"
    )
    
    # Work & Productivity (Productivity Agent)
    work_hours = models.JSONField(
        default=dict, blank=True,
        help_text="e.g. {'start': '09:00', 'end': '18:00', 'days': ['Mon','Tue','Wed','Thu','Fri']}"
    )
    
    # Wellness (Wellness Agent)
    fitness_level = models.CharField(
        max_length=20, 
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='intermediate'
    )
    health_conditions = models.JSONField(
        default=list, blank=True,
        help_text="List of conditions agents should be aware of"
    )
    
    # Study (Study Agent)
    learning_style = models.CharField(
        max_length=20,
        choices=[
            ('visual', 'Visual'),
            ('auditory', 'Auditory'),
            ('reading', 'Reading/Writing'),
            ('kinesthetic', 'Kinesthetic'),
        ],
        default='visual'
    )
    
    # Goals — the big picture that ties all agents together
    goals = models.JSONField(
        default=list, blank=True,
        help_text="e.g. [{'goal': 'Lose 5kg', 'deadline': '2026-06-01', 'category': 'wellness'}]"
    )
    
    # Free-form notes for agents
    about_me = models.TextField(
        blank=True, default='',
        help_text="Anything the user wants agents to always know about them"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile: {self.user.email}"
    
    def get_agent_context(self, agent_type: str | None = None) -> dict:
        """
        Build a context dict that can be injected into any agent's system prompt.
        Optionally filter by agent_type for agent-specific preferences.
        """
        context = {
            'name': self.user.get_full_name(),
            'timezone': self.timezone,
            'goals': self.goals,
            'about_me': self.about_me,
        }
        
        if agent_type in ('meal_planner_agent', None):
            context['dietary_preferences'] = self.dietary_preferences
            
        if agent_type in ('productivity_agent', None):
            context['work_hours'] = self.work_hours
            
        if agent_type in ('wellness_agent', None):
            context['fitness_level'] = self.fitness_level
            context['health_conditions'] = self.health_conditions
            
        if agent_type in ('study_agent', None):
            context['learning_style'] = self.learning_style
        
        return context


class AgentSession(models.Model):
    """Store agent conversation sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    agent_type = models.CharField(max_length=50, choices=[
        ('meal_planner', 'Meal Planner'),
        ('productivity', 'Productivity Agent'),
        ('study_buddy', 'Study Buddy'),
        ('wellness', 'Wellness Agent'),
        ('habit_coach', 'Habit Coach'),
        ('orchestrator', 'Orchestrator'),
    ])
    session_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.agent_type} - {self.session_id}"


class Message(models.Model):
    """Store individual messages in agent conversations"""
    session = models.ForeignKey(AgentSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=[
        ('user', 'User'),
        ('agent', 'Agent'),
        ('system', 'System'),
    ])
    content = models.TextField()
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class MealPlan(models.Model):
    """Store meal plans generated by the meal planner agent"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(AgentSession, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=[
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ])
    meal_name = models.CharField(max_length=200)
    ingredients = models.JSONField(null=True, blank=True)
    instructions = models.TextField(null=True, blank=True)
    nutritional_info = models.JSONField(null=True, blank=True)
    preferences = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date', 'meal_type']
    
    def __str__(self):
        return f"{self.meal_name} - {self.date}"


class Task(models.Model):
    """Store tasks managed by productivity agent"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(AgentSession, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    status = models.CharField(max_length=20, choices=[
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='todo')
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'due_date']
    
    def __str__(self):
        return self.title


class StudySession(models.Model):
    """Store study sessions from study buddy agent"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(AgentSession, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=200)
    topic = models.CharField(max_length=200, null=True, blank=True)
    duration = models.IntegerField(help_text="Duration in minutes")
    notes = models.TextField(null=True, blank=True)
    resources = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.created_at.date()}"


class WellnessActivity(models.Model):
    """Store wellness activities tracked by wellness agent"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(AgentSession, on_delete=models.SET_NULL, null=True, blank=True)
    activity_type = models.CharField(max_length=50, choices=[
        ('exercise', 'Exercise'),
        ('meditation', 'Meditation'),
        ('sleep', 'Sleep'),
        ('hydration', 'Hydration'),
        ('mood', 'Mood'),
    ])
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in minutes")
    intensity = models.CharField(max_length=20, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    recorded_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']
        verbose_name_plural = 'Wellness Activities'
    
    def __str__(self):
        return f"{self.activity_type} - {self.recorded_at.date()}"


class Event(models.Model):
    """Store events in the message bus pattern"""
    EVENT_TYPES = [
        ('INTENT_RECEIVED', 'Intent Received'),
        ('AGENT_SELECTED', 'Agent Selected'),
        ('CONTEXT_FETCHED', 'Context Fetched'),
        ('AGENT_RESPONSE', 'Agent Response'),
        ('ACTIONS_APPLIED', 'Actions Applied'),
        ('AUDIT_LOGGED', 'Audit Logged'),
        ('ERROR_OCCURRED', 'Error Occurred'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    session = models.ForeignKey(AgentSession, on_delete=models.CASCADE, related_name='events')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    payload = models.JSONField(help_text="Event data and context")
    metadata = models.JSONField(null=True, blank=True, help_text="Additional metadata")
    timestamp = models.DateTimeField(auto_now_add=True)
    parent_event = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_events')
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['session', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.timestamp}"


class AuditLog(models.Model):
    """Comprehensive audit trail for all system activities"""
    ACTION_TYPES = [
        ('USER_ACTION', 'User Action'),
        ('AGENT_ACTION', 'Agent Action'),
        ('SYSTEM_ACTION', 'System Action'),
        ('DATA_MODIFICATION', 'Data Modification'),
        ('AUTHENTICATION', 'Authentication'),
    ]
    
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session = models.ForeignKey(AgentSession, on_delete=models.SET_NULL, null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=200, help_text="Description of the action")
    resource = models.CharField(max_length=200, null=True, blank=True, help_text="Resource affected (e.g., Task:123)")
    details = models.JSONField(help_text="Detailed information about the action")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['session', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action_type} - {self.action} - {self.timestamp}"


class AgentContext(models.Model):
    """Store context information for agent interactions"""
    session = models.ForeignKey(AgentSession, on_delete=models.CASCADE, related_name='contexts')
    context_type = models.CharField(max_length=50, choices=[
        ('USER_PREFERENCES', 'User Preferences'),
        ('CONVERSATION_HISTORY', 'Conversation History'),
        ('TASK_CONTEXT', 'Task Context'),
        ('TEMPORAL_CONTEXT', 'Temporal Context'),
        ('CUSTOM', 'Custom'),
    ])
    key = models.CharField(max_length=100, help_text="Context key identifier")
    value = models.JSONField(help_text="Context data")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When this context expires")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['session', 'context_type', 'key']
        indexes = [
            models.Index(fields=['session', 'context_type']),
        ]
    
    def __str__(self):
        return f"{self.context_type} - {self.key}"


class Habit(models.Model):
    """
    Recurring habits tracked by the Habit Coach agent.
    This is the stickiness feature — streaks drive daily engagement.
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekdays', 'Weekdays'),
        ('weekends', 'Weekends'),
        ('weekly', 'Weekly'),
        ('custom', 'Custom'),
    ]
    
    CATEGORY_CHOICES = [
        ('health', 'Health & Fitness'),
        ('productivity', 'Productivity'),
        ('mindfulness', 'Mindfulness'),
        ('learning', 'Learning'),
        ('social', 'Social'),
        ('self_care', 'Self Care'),
        ('finance', 'Finance'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    # For 'custom' frequency: which days (0=Mon, 6=Sun)
    custom_days = models.JSONField(default=list, blank=True, help_text="e.g. [0,2,4] for Mon/Wed/Fri")
    
    # Time-based
    reminder_time = models.TimeField(null=True, blank=True, help_text="When to remind the user")
    target_count = models.IntegerField(default=1, help_text="How many times per day (e.g., 8 glasses of water)")
    
    # Streak tracking
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    total_completions = models.IntegerField(default=0)
    
    # UI
    color = models.CharField(max_length=7, default='#8B5CF6', help_text="Hex color for UI display")
    icon = models.CharField(max_length=10, default='✅', help_text="Emoji icon")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-current_streak', 'name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.icon} {self.name} (streak: {self.current_streak})"
    
    def calculate_streak(self):
        """Recalculate current streak from HabitLog entries."""
        from datetime import date, timedelta
        
        today = date.today()
        streak = 0
        check_date = today
        
        while True:
            log = self.logs.filter(date=check_date, completed=True).exists()
            if log:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                # Allow today to be incomplete (streak isn't broken until tomorrow)
                if check_date == today:
                    check_date -= timedelta(days=1)
                    continue
                break
        
        self.current_streak = streak
        if streak > self.best_streak:
            self.best_streak = streak
        self.save(update_fields=['current_streak', 'best_streak'])
        return streak


class HabitLog(models.Model):
    """Daily completion log for a habit. One entry per habit per day."""
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField()
    completed = models.BooleanField(default=False)
    count = models.IntegerField(default=0, help_text="For countable habits (e.g., glasses of water)")
    notes = models.TextField(blank=True, default='')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['habit', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['habit', 'date']),
        ]
    
    def __str__(self):
        status = '✅' if self.completed else '⬜'
        return f"{status} {self.habit.name} — {self.date}"

