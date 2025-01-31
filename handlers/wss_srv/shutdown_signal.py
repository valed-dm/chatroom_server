import asyncio
import functools
import logging
import signal
import threading


class ShutdownSignalHandler:
    """Handles system shutdown signals and stores the shutdown reason."""

    DEFAULT_REASON = "Unknown"

    def __init__(self):
        self._reason = self.DEFAULT_REASON
        self._stop_event = asyncio.Event()
        self._lock = threading.Lock()

    def handle_signal(self, signum):
        """Handles shutdown signals and updates the shutdown reason."""
        with self._lock:  # Ensure thread-safe updates
            if signum == signal.SIGTERM:
                self._reason = "Planned maintenance"
            elif signum == signal.SIGINT:
                self._reason = "Manual shutdown (CTRL+C)"
            else:
                self._reason = f"Stopped due to signal {signum}"

        logging.info(f"Shutdown signal received (signal={signum}): {self._reason}")
        self._stop_event.set()  # Trigger shutdown

    async def register_signals(self):
        """Registers signal handlers for SIGINT and SIGTERM."""
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, functools.partial(self.handle_signal, sig))

    @property
    def reason(self):
        """Returns the shutdown reason."""
        return self._reason

    @property
    def stop_event(self):
        """Returns the shutdown event."""
        return self._stop_event
