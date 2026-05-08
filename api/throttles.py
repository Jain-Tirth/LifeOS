from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import Throttled

class AgentMessageThrottle(UserRateThrottle):
    """
    Rate limit agent messages to prevent cost explosion.
    Implements: 10 messages per minute per user (DDIA Ch8: Overload Control).
    """
    scope = 'agent_message'
    rate = '10/min'

    def throttle_success(self):
        """Called after rate check passes"""
        return super().throttle_success()

class AgentSessionThrottle(UserRateThrottle):
    """
    Rate limit session creation to prevent resource exhaustion.
    Implements: 5 sessions per hour per user.
    """
    scope = 'agent_session'
    rate = '5/hour'

class BurstThrottle(UserRateThrottle):
    """
    Detect burst attacks: 100+ requests in 10 seconds.
    """
    scope = 'burst'

    # We change 10sec to something DRF can parse natively for rate, or we parse it custom.
    # Native DRF parse_rate expects 's', 'm', 'h', 'd' as period.
    # E.g., '100/min', '10/s'.
    # We will use '10/s' to be 10 requests per second.
    rate = '10/s'
