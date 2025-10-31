# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# AIA: Primarily AI, Modified content, Human-initiated, Reviewed, Claude (Anthropic AI) via Cursor
# AIA PAI Mc Hin R Claude Cursor - https://aiattribution.github.io/interpret-attribution

# Python
import json
import logging
import redis

# Django
from django.conf import settings

__all__ = ['CallbackQueueDispatcher']


# use a custom JSON serializer so we can properly handle !unsafe and !vault
# objects that may exist in events emitted by the callback plugin
# see: https://github.com/ansible/ansible/pull/38759
class AnsibleJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if getattr(o, 'yaml_tag', None) == '!vault':
            return o.data
        return super(AnsibleJSONEncoder, self).default(o)


class CallbackQueueDispatcher(object):
    def __init__(self):
        self.queue = getattr(settings, 'CALLBACK_QUEUE', '')
        self.logger = logging.getLogger('awx.main.queue.CallbackQueueDispatcher')
        self._broker_url = settings.BROKER_URL
        self.connection = redis.Redis.from_url(self._broker_url)
        self._connection_failures = 0
        self._max_reconnect_attempts = 3
        self._total_reconnections = 0
        self._events_lost = 0

    def _reconnect(self):
        """
        Attempt to reconnect to Redis after connection failure.

        Returns:
            bool: True if reconnection successful, False otherwise
        """
        try:
            attempt = self._connection_failures + 1
            self.logger.warning(
                f"Redis reconnection attempt {attempt}/{self._max_reconnect_attempts} " f"(total reconnections this session: {self._total_reconnections})"
            )

            # Create new connection
            self.connection = redis.Redis.from_url(self._broker_url)

            # Verify connection works
            self.connection.ping()

            # Success
            self._connection_failures = 0
            self._total_reconnections += 1
            self.logger.info(f"Successfully reconnected to Redis (session reconnections: {self._total_reconnections})")
            return True

        except Exception as e:
            self._connection_failures += 1
            self.logger.error(f"Redis reconnection failed (attempt {self._connection_failures}): {type(e).__name__}: {e}")
            return False

    def dispatch(self, obj):
        """
        Dispatch event to Redis queue with automatic reconnection on failure.

        Handles BrokenPipeError and ConnectionError by attempting reconnection.
        If all reconnection attempts fail, logs the event loss but allows job to continue.

        Args:
            obj: Event data to dispatch (dict or serializable object)
        """
        max_attempts = self._max_reconnect_attempts + 1
        last_error = None

        # Extract diagnostic info from event
        event_type = 'unknown'
        job_id = 'unknown'
        if isinstance(obj, dict):
            event_type = obj.get('event', obj.get('event_name', 'unknown'))
            job_id = obj.get('job_id', obj.get('unified_job_id', 'unknown'))

        for attempt in range(max_attempts):
            try:
                # Attempt to push event to Redis
                self.connection.rpush(self.queue, json.dumps(obj, cls=AnsibleJSONEncoder))

                # Success - reset failure counter if this was a recovery
                if self._connection_failures > 0:
                    self.logger.info(f"Redis connection recovered after reconnection. " f"job_id={job_id}, event_type={event_type}")
                    self._connection_failures = 0

                return  # Successfully dispatched

            except (BrokenPipeError, redis.exceptions.ConnectionError) as e:
                last_error = e
                error_type = type(e).__name__

                self.logger.warning(f"Redis connection error during event dispatch " f"(attempt {attempt + 1}/{max_attempts}): {error_type}: {e}")

                # Enhanced diagnostics
                self.logger.warning(
                    f"Failed event details: job_id={job_id}, event_type={event_type}, " f"queue={self.queue}, attempt={attempt + 1}/{max_attempts}"
                )

                if attempt < max_attempts - 1:
                    # Try to reconnect before next attempt
                    reconnected = self._reconnect()
                    if reconnected:
                        self.logger.info("Retrying event dispatch after successful reconnection")
                    else:
                        self.logger.warning(f"Reconnection failed, will retry dispatch anyway " f"(attempt {attempt + 2} coming)")
                    # Continue to next attempt
                    continue
                else:
                    # All attempts exhausted
                    self._events_lost += 1
                    self.logger.error(
                        f"CRITICAL: Failed to dispatch event after {max_attempts} attempts. "
                        f"Event will be lost. Total events lost this session: {self._events_lost}"
                    )
                    self.logger.error(
                        f"DIAGNOSTIC INFO: "
                        f"job_id={job_id}, "
                        f"event_type={event_type}, "
                        f"queue={self.queue}, "
                        f"broker_url={self._broker_url}, "
                        f"last_error={error_type}: {last_error}, "
                        f"session_reconnections={self._total_reconnections}, "
                        f"session_events_lost={self._events_lost}"
                    )

                    # IMPORTANT: Don't raise exception
                    # Allow job to continue even though this event was lost
                    # This prevents losing 17+ minutes of work due to event logging failure
                    break

            except Exception as e:
                # Catch any other unexpected Redis errors
                self.logger.error(f"Unexpected error dispatching event to Redis: {type(e).__name__}: {e}")
                self.logger.error(f"Event context: job_id={job_id}, event_type={event_type}")
                # Don't raise - allow job to continue
                break

    def health_check(self):
        """
        Check Redis connection health.

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            self.connection.ping()
            return True
        except Exception as e:
            self.logger.warning(f"Redis health check failed: {type(e).__name__}: {e}")
            return False

    def get_connection_stats(self):
        """
        Get Redis connection statistics for monitoring.

        Returns:
            dict: Connection statistics
        """
        return {
            'broker_url': self._broker_url,
            'queue': self.queue,
            'connected': self.health_check(),
            'connection_failures': self._connection_failures,
            'total_reconnections': self._total_reconnections,
            'events_lost': self._events_lost,
        }
