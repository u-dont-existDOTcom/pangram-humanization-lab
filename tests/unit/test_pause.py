import os
import signal
import sys
import threading
from pathlib import Path

import pytest

from authorial_flow.pause import (
    OperationContext,
    OwnerPauseRequested,
    PauseController,
    temporary_sigint_pause,
)
from authorial_flow.process_runner import ProcessRunner, ProcessSpec


def test_requested_pause_terminates_child_and_discards_partial_output():
    controller = PauseController()
    started = threading.Event()
    caught = []
    runner = ProcessRunner(
        heartbeat_seconds=0.05,
        pause_controller=controller,
        on_start=lambda _payload: started.set(),
    )

    def invoke():
        try:
            runner.run(ProcessSpec(
                argv=[sys.executable, "tests/fixtures/silent_child.py", "5"],
                cwd=Path.cwd(),
                timeout_seconds=10,
                operation=OperationContext(
                    node="generation",
                    operation="model_call",
                    provider="claude",
                    model="claude-opus-5",
                    role="writer",
                    cancelable=True,
                ),
            ))
        except OwnerPauseRequested as exc:
            caught.append(exc)

    worker = threading.Thread(target=invoke)
    worker.start()
    assert started.wait(2)
    controller.request()
    worker.join(3)

    assert not worker.is_alive()
    assert len(caught) == 1
    assert caught[0].partial_output_discarded is True
    assert caught[0].operation.role == "writer"
    with pytest.raises(ProcessLookupError):
        os.kill(caught[0].pid, 0)


def test_pause_requested_before_spawn_starts_no_child():
    controller = PauseController()
    controller.request()
    starts = []
    runner = ProcessRunner(
        heartbeat_seconds=0.1,
        pause_controller=controller,
        on_start=starts.append,
    )

    with pytest.raises(OwnerPauseRequested):
        runner.run(ProcessSpec(
            argv=[sys.executable, "tests/fixtures/silent_child.py", "0.1"],
            cwd=Path.cwd(),
            timeout_seconds=2,
            operation=OperationContext(
                node="generation",
                operation="model_call",
                cancelable=True,
            ),
        ))

    assert starts == []


def test_non_cancelable_process_finishes_and_leaves_pause_pending():
    controller = PauseController()
    controller.request()
    starts = []
    runner = ProcessRunner(
        heartbeat_seconds=0.05,
        pause_controller=controller,
        on_start=starts.append,
    )

    result = runner.run(ProcessSpec(
        argv=[sys.executable, "tests/fixtures/silent_child.py", "0.05"],
        cwd=Path.cwd(),
        timeout_seconds=2,
        operation=OperationContext(
            node="detector",
            operation="atomic_checkpoint",
            cancelable=False,
        ),
    ))

    assert result.returncode == 0
    assert result.stdout.endswith("finished\n")
    assert len(starts) == 1
    assert controller.requested() is True


def test_pause_controller_observes_current_operation_and_acknowledges_request():
    controller = PauseController()
    operation = OperationContext(
        node="generation",
        operation="model_call",
        provider="codex",
        model="gpt-5.6-sol",
        role="fidelity",
        cancelable=True,
    )

    with controller.operation(operation):
        assert controller.observe().operation == operation
        requested = controller.request()
        assert requested.requested is True
        assert requested.requested_at > 0
        assert requested.operation == operation

    assert controller.observe().operation is None
    controller.acknowledge()
    assert controller.requested() is False


def test_temporary_sigint_handler_requests_pause_and_restores_previous_handler():
    controller = PauseController()
    observations = []
    previous = signal.getsignal(signal.SIGINT)

    with temporary_sigint_pause(controller, observations.append):
        signal.raise_signal(signal.SIGINT)
        assert controller.requested() is True
        assert len(observations) == 1
        assert observations[0].requested is True

    assert signal.getsignal(signal.SIGINT) is previous
