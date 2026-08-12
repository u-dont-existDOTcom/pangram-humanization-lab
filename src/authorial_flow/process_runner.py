from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
from collections.abc import Callable, Mapping

from .pause import OperationContext, OwnerPauseRequested, PauseController


@dataclass(frozen=True)
class ProcessSpec:
    argv: list[str]
    cwd: Path
    timeout_seconds: float
    env: Mapping[str, str] | None = None
    input_text: str | None = None
    terminate_grace_seconds: float = 0.5
    operation: OperationContext | None = None


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    pid: int
    duration_seconds: float
    termination_reason: str


class ProcessRunner:
    def __init__(
        self,
        heartbeat_seconds: float = 10,
        on_heartbeat: Callable[[dict], None] | None = None,
        pause_controller: PauseController | None = None,
        on_start: Callable[[dict], None] | None = None,
    ) -> None:
        if heartbeat_seconds <= 0:
            raise ValueError("heartbeat_seconds must be > 0")
        self.heartbeat_seconds = heartbeat_seconds
        self.on_heartbeat = on_heartbeat
        self.pause_controller = pause_controller
        self.on_start = on_start

    def _heartbeat(
        self,
        proc: subprocess.Popen[bytes],
        started: float,
        operation: OperationContext,
    ) -> None:
        if self.on_heartbeat:
            self.on_heartbeat({
                "pid": proc.pid,
                "elapsed_seconds": max(0.0, time.monotonic() - started),
                "alive": proc.poll() is None,
                "node": operation.node,
                "operation": operation.operation,
                "provider": operation.provider,
                "model": operation.model,
                "role": operation.role,
            })

    @staticmethod
    def _terminate(proc: subprocess.Popen[bytes], grace: float) -> None:
        if proc.poll() is not None:
            return
        try:
            proc.terminate()
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=max(0.01, grace))
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            proc.wait(timeout=2)

    def run(self, spec: ProcessSpec) -> ProcessResult:
        operation = spec.operation or OperationContext()
        if (
            operation.cancelable
            and self.pause_controller is not None
            and self.pause_controller.requested()
        ):
            raise OwnerPauseRequested(operation)
        if self.pause_controller is not None:
            with self.pause_controller.operation(operation):
                return self._run(spec, operation)
        return self._run(spec, operation)

    def _run(self, spec: ProcessSpec, operation: OperationContext) -> ProcessResult:
        started = time.monotonic()
        proc = subprocess.Popen(
            spec.argv,
            cwd=str(spec.cwd),
            env=dict(spec.env) if spec.env is not None else None,
            stdin=subprocess.PIPE if spec.input_text is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            start_new_session=True,
        )
        if self.on_start is not None:
            self.on_start({
                "pid": proc.pid,
                "node": operation.node,
                "operation": operation.operation,
                "provider": operation.provider,
                "model": operation.model,
                "role": operation.role,
            })
        assert proc.stdout is not None and proc.stderr is not None
        if spec.input_text is not None and proc.stdin is not None:
            proc.stdin.write(spec.input_text.encode("utf-8"))
            proc.stdin.flush()
            proc.stdin.close()
        os.set_blocking(proc.stdout.fileno(), False)
        os.set_blocking(proc.stderr.fileno(), False)
        selector = selectors.DefaultSelector()
        selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
        selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
        chunks: dict[str, list[bytes]] = {"stdout": [], "stderr": []}
        next_heartbeat = started + self.heartbeat_seconds
        termination_reason = "exit"

        def drain_ready(timeout: float) -> None:
            for key, _ in selector.select(timeout):
                stream = key.fileobj
                try:
                    data = os.read(stream.fileno(), 65536)
                except BlockingIOError:
                    continue
                if data:
                    chunks[key.data].append(data)
                else:
                    try:
                        selector.unregister(stream)
                    except Exception:
                        pass

        try:
            while True:
                now = time.monotonic()
                elapsed = now - started
                if (
                    operation.cancelable
                    and self.pause_controller is not None
                    and self.pause_controller.requested()
                ):
                    termination_reason = "owner_pause"
                    self._terminate(proc, spec.terminate_grace_seconds)
                    raise OwnerPauseRequested(operation, pid=proc.pid)
                if elapsed >= spec.timeout_seconds and proc.poll() is None:
                    termination_reason = "timeout"
                    self._terminate(proc, spec.terminate_grace_seconds)

                wait_until = min(
                    max(0.0, next_heartbeat - now),
                    0.05,
                )
                drain_ready(wait_until)

                if (
                    operation.cancelable
                    and self.pause_controller is not None
                    and self.pause_controller.requested()
                ):
                    termination_reason = "owner_pause"
                    self._terminate(proc, spec.terminate_grace_seconds)
                    raise OwnerPauseRequested(operation, pid=proc.pid)

                now = time.monotonic()
                if now >= next_heartbeat and proc.poll() is None:
                    self._heartbeat(proc, started, operation)
                    while next_heartbeat <= now:
                        next_heartbeat += self.heartbeat_seconds

                if proc.poll() is not None:
                    # Drain remaining pipe bytes until EOF or a short quiet period.
                    quiet = 0
                    while selector.get_map() and quiet < 4:
                        before = sum(len(x) for v in chunks.values() for x in v)
                        drain_ready(0.02)
                        after = sum(len(x) for v in chunks.values() for x in v)
                        quiet = quiet + 1 if after == before else 0
                    break
        except KeyboardInterrupt:
            termination_reason = "interrupt"
            self._terminate(proc, spec.terminate_grace_seconds)
            self._heartbeat(proc, started, operation)
            raise
        finally:
            selector.close()
            for stream in (proc.stdout, proc.stderr):
                try:
                    stream.close()
                except Exception:
                    pass

        duration = time.monotonic() - started
        return ProcessResult(
            returncode=int(proc.returncode if proc.returncode is not None else -1),
            stdout=b"".join(chunks["stdout"]).decode("utf-8", errors="replace"),
            stderr=b"".join(chunks["stderr"]).decode("utf-8", errors="replace"),
            pid=proc.pid,
            duration_seconds=duration,
            termination_reason=termination_reason,
        )
