from __future__ import annotations

import time
from collections import defaultdict, deque

MAX_CHAT_LEN = 200
CHAT_RATE_LIMIT = 5
CHAT_RATE_WINDOW_SECONDS = 5.0


class ChatError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def sanitize_chat_message(raw: object) -> str:
    if not isinstance(raw, str):
        raise ChatError("Message must be a string")
    cleaned = []
    for char in raw:
        code = ord(char)
        if char in "\r\n\t":
            cleaned.append(" ")
        elif 32 <= code != 127:
            cleaned.append(char)
    text = " ".join("".join(cleaned).split())
    if not text:
        raise ChatError("Message cannot be empty")
    if len(text) > MAX_CHAT_LEN:
        raise ChatError(f"Message must be {MAX_CHAT_LEN} characters or fewer")
    return text


def utc_timestamp() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RateLimiter:
    def __init__(
        self,
        max_messages: int = CHAT_RATE_LIMIT,
        window_seconds: float = CHAT_RATE_WINDOW_SECONDS,
    ) -> None:
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_messages:
            return False
        hits.append(now)
        return True

    def forget(self, key: str) -> None:
        self._hits.pop(key, None)

    def clear(self) -> None:
        self._hits.clear()
