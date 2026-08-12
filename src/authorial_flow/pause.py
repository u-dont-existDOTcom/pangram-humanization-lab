from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import signal
import threading
import time


@dataclass(frozen=True)
class OperationContext:
    node: str = ""
    operation: str = ""
    provider: str = ""
    model: str = ""
    role: str = ""
    cancelable: bool = False


@dataclass(frozen=True)
class PauseObservation:
    requested: bool
    requested_at: float
    operation: OperationContext | None


class OwnerPauseRequested(RuntimeError):
    def __init__(self, operation: OperationContext, *, pid: int = 0) -> None:
        self.operation = operation
        self.pid = pid
        self.partial_output_discarded = True
        super().__init__("owner requested a checkpointed supervisor pause")


class PauseController:
    def __init__(self) -> None:
        self._requested = threading.Event()
        self._lock = threading.RLock()
        self._requested_at = 0.0
        self._operation: OperationContext | None = None

    def request(self) -> PauseObservation:
        with self._lock:
            if not self._requested.is_set():
                self._requested_at = time.time()
                self._requested.set()
            return self.observe()

    def observe(self) -> PauseObservation:
        with self._lock:
            return PauseObservation(
                self._requested.is_set(),
                self._requested_at,
                self._operation,
            )

    def requested(self) -> bool:
        return self._requested.is_set()

    def acknowledge(self) -> None:
        with self._lock:
            self._requested.clear()
            self._requested_at = 0.0

    @contextmanager
    def operation(self, value: OperationContext) -> Iterator[None]:
        with self._lock:
            self._operation = value
        try:
            yield
        finally:
            with self._lock:
                self._operation = None


@contextmanager
def temporary_sigint_pause(
    controller: PauseController,
    on_request: Callable[[PauseObservation], None],
) -> Iterator[None]:
    previous = signal.getsignal(signal.SIGINT)

    def handler(_signum, _frame) -> None:
        on_request(controller.request())

    signal.signal(signal.SIGINT, handler)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, previous)
