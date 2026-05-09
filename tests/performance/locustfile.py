from locust import HttpUser, task, between

class LifeOSUser(HttpUser):
    """Simulated user behavior for load testing"""
    wait_time = between(1, 5)

    def on_start(self):
        """Authenticate and get token"""
        # For a real load test we'd login or get a token.
        # Here we mock the behavior based on the expected endpoints.

        # We need a user to load test, so we assume an existing test user or create one
        # In a real environment, you'd likely create a bunch of users in setup
        self.email = f'loadtest_{id(self)}@test.com'
        self.password = 'loadtest123'

        # Try to register
        self.client.post('/api/v1/auth/register/', json={
            'email': self.email,
            'password': self.password,
            'first_name': 'Load',
            'last_name': 'Test'
        })

        # Login
        response = self.client.post('/api/v1/auth/login/', json={
            'email': self.email,
            'password': self.password
        })

        if response.status_code == 200:
            self.token = response.json().get('access')
            self.client.headers.update({
                'Authorization': f'Bearer {self.token}'
            })

    @task(1)
    def create_session(self):
        """Create new agent session"""
        response = self.client.post(
            '/api/v1/create-session/',
            json={'agent_type': 'meal_planner'}
        )

        if response.status_code == 201:
            self.session_id = response.json().get('id') or response.json().get('session_id')

    @task(5)
    def send_message(self):
        """Send message to agent"""
        if hasattr(self, 'session_id'):
            self.client.post(
                f'/api/v1/sessions/{self.session_id}/send_message/',
                json={'content': 'What should I eat for dinner?'}
            )

    @task(2)
    def get_habit_digest(self):
        """Get daily habit summary"""
        self.client.get('/api/v1/habits/daily_digest/')

# Run: locust -f tests/performance/locustfile.py --host=http://localhost:8000
