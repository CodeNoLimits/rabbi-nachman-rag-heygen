"""
Rate limiter simple pour l'API
"""

import time
from collections import defaultdict
from typing import Dict
from fastapi import HTTPException, Request
from loguru import logger


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, per_minute: int = 30, per_hour: int = 500):
        self.per_minute = per_minute
        self.per_hour = per_hour

        # Storage: {client_id: [(timestamp, count)]}
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)

    def check_rate_limit(self, request: Request) -> str:
        """
        Check rate limit pour une requête

        Args:
            request: FastAPI Request

        Returns:
            client_id si autorisé

        Raises:
            HTTPException si rate limit dépassé
        """
        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"

        current_time = time.time()

        # Clean old entries
        self._clean_old_entries(client_id, current_time)

        # Check minute limit
        minute_count = len(self.minute_requests[client_id])
        if minute_count >= self.per_minute:
            logger.warning(f"Rate limit exceeded (minute) for {client_id}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.per_minute} requests per minute"
            )

        # Check hour limit
        hour_count = len(self.hour_requests[client_id])
        if hour_count >= self.per_hour:
            logger.warning(f"Rate limit exceeded (hour) for {client_id}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.per_hour} requests per hour"
            )

        # Add current request
        self.minute_requests[client_id].append(current_time)
        self.hour_requests[client_id].append(current_time)

        return client_id

    def _clean_old_entries(self, client_id: str, current_time: float):
        """Nettoyer les entrées anciennes"""
        # Clean minute entries (older than 60s)
        self.minute_requests[client_id] = [
            ts for ts in self.minute_requests[client_id]
            if current_time - ts < 60
        ]

        # Clean hour entries (older than 3600s)
        self.hour_requests[client_id] = [
            ts for ts in self.hour_requests[client_id]
            if current_time - ts < 3600
        ]

    def get_stats(self, client_id: str) -> Dict[str, int]:
        """Obtenir les stats pour un client"""
        current_time = time.time()
        self._clean_old_entries(client_id, current_time)

        return {
            'requests_last_minute': len(self.minute_requests[client_id]),
            'requests_last_hour': len(self.hour_requests[client_id]),
            'limit_per_minute': self.per_minute,
            'limit_per_hour': self.per_hour
        }
