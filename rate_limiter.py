"""Global rate limiter for Discord API requests to respect bot rate limits."""

import asyncio
import time
from collections import deque
from typing import Optional


class GlobalRateLimiter:
	"""
	Implements a token bucket algorithm to prevent hitting Discord's global rate limit.
	
	Discord allows bots 50 requests per second. This limiter ensures the bot stays
	well below that threshold by queuing and throttling requests.
	
	The limiter tracks requests across a moving window and uses asyncio to coordinate
	access across concurrent commands.
	"""
	
	def __init__(self, max_requests_per_second: int = 45):
		"""
		Initialize the rate limiter.
		
		Args:
			max_requests_per_second: Target requests per second (default 45, discord limit is 50).
		"""
		self.max_requests = max_requests_per_second
		self.window_size = 1.0  # 1 second
		self.request_times = deque()  # Track request timestamps
		self.lock = asyncio.Lock()
	
	async def acquire(self) -> None:
		"""
		Acquire permission to make a request. Blocks if rate limit would be exceeded.
		"""
		async with self.lock:
			now = time.time()
			
			# Remove timestamps outside the current window
			while self.request_times and self.request_times[0] < now - self.window_size:
				self.request_times.popleft()
			
			# If we've hit the limit, calculate how long to wait
			while len(self.request_times) >= self.max_requests:
				# Wait until the oldest request falls outside the window
				oldest_time = self.request_times[0]
				sleep_time = (oldest_time + self.window_size - now) + 0.01
				
				# Release lock while we sleep to allow other tasks to check
				await asyncio.sleep(sleep_time)
				
				# Re-acquire and recalculate
				now = time.time()
				while self.request_times and self.request_times[0] < now - self.window_size:
					self.request_times.popleft()
			
			# Record this request
			self.request_times.append(now)
	
	def get_requests_in_last_second(self) -> int:
		"""Get the number of requests made in the last second."""
		now = time.time()
		while self.request_times and self.request_times[0] < now - self.window_size:
			self.request_times.popleft()
		return len(self.request_times)


# Global instance
_global_limiter: Optional[GlobalRateLimiter] = None


def get_global_limiter() -> GlobalRateLimiter:
	"""Get or create the global rate limiter instance."""
	global _global_limiter
	if _global_limiter is None:
		_global_limiter = GlobalRateLimiter()
	return _global_limiter
