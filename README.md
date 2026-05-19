# CoreRunner

`CoreRunner` is the process-group-safe subprocess library for the ProtocolWarden ecosystem. It provides two surfaces:

1. **`safe_run()` primitive** — standalone, no RxP dependency. Used by TeamExecutor, DAGExecutor, and CritiqueExecutor to replace raw `subprocess.run()` calls with full process-group safety.
2. **`CoreRunner.run(invocation)`** — full RxP invocation runner (stdout/stderr capture to files, ArtifactDescriptor production). Used by OperationsCenter's `direct_local` and `aider_local` adapters.

```text
safe_run(cmd, ...)    →  SafeRunResult            # lightweight primitive
CoreRunner.run(inv)   →  RuntimeResult            # full RxP path

RuntimeInvocation → CoreRunner.run → RuntimeResult
                       ├─ "subprocess" → SubprocessRunner → safe_run()
                       ├─ "manual"     → ManualRunner (caller-supplied dispatcher)
                       └─ "http"       → HttpRunner   (sync request/response)
```

## What this repo is

- Process-group-safe subprocess execution (`start_new_session=True`, `os.killpg(SIGKILL)` on timeout, transient SIGTERM handler that reaps child group on supervisor death)
- Standalone `safe_run()` primitive — no RxP types, no artifact descriptors; just `SafeRunResult(returncode, stdout, stderr, timed_out)`
- Environment overlay, working directory control, timeout enforcement
- Stdout/stderr capture to files and ArtifactDescriptor collection (RxP path only)
- Dispatch-by-`runtime_kind` registry

## What this repo is not

- OperationsCenter — orchestration, planning, policy
- SwitchBoard — lane/backend selection
- TeamExecutor / DAGExecutor / CritiqueExecutor — AI execution backends (they consume `safe_run()`)
- a scheduler / queue system / fork manager / agent framework

## Quick start

```bash
pip install -e .
```

### Primitive (no RxP dependency)

```python
from core_runner.process import safe_run

result = safe_run(["python", "-c", "print('hello')"], timeout_seconds=30)
print(result.returncode)  # 0
print(result.stdout)      # "hello\n"
print(result.timed_out)   # False
```

### Full RxP path

```python
from core_runner import CoreRunner
result = CoreRunner().run(invocation)   # → RuntimeResult
```

## Architecture

`safe_run()` is the execution primitive — it owns all process-group logic. `SubprocessRunner` delegates to `safe_run()` and adds the file-capture / ArtifactDescriptor layer. `CoreRunner.run(invocation)` reads `invocation.runtime_kind` and forwards to a registered runner.

## Runners

| Runner | runtime_kind | What it does |
|---|---|---|
| `SubprocessRunner` | `subprocess` | Local subprocess via `safe_run()`. Default registered runner. |
| `ManualRunner` | `manual` | Forwards invocation to a caller-supplied dispatcher callable. |
| `HttpRunner` | `http` | Synchronous HTTP request/response. |
| `AsyncHttpRunner` | `http_async` | 202 kickoff + poll-until-terminal. |

## Example usage

### safe_run() — primitive

```python
from core_runner.process import safe_run

result = safe_run(
    ["python", "script.py", "--arg", "value"],
    cwd="/path/to/project",
    env={"MY_VAR": "value"},
    timeout_seconds=60,
)
if result.timed_out:
    print("timed out")
elif result.returncode != 0:
    print(f"failed: {result.stderr}")
```

### CoreRunner — subprocess (default)

```python
from core_runner import CoreRunner
from core_runner.contracts import RuntimeInvocation

runtime = CoreRunner()

result = runtime.run(
    RuntimeInvocation(
        invocation_id="example-001",
        runtime_name="local-echo",
        runtime_kind="subprocess",
        working_directory=".",
        command=["python", "-c", "print('hello')"],
        environment={},
        timeout_seconds=30,
        input_payload_path=None,
        output_result_path=None,
        artifact_directory=None,
        metadata={},
    )
)
print(result.status)  # "succeeded"
```

### CoreRunner — manual (out-of-process service)

```python
from core_runner import CoreRunner
from core_runner.runners import ManualRunner

def my_dispatcher(invocation):
    raw = call_external_service(...)
    return synthesize_runtime_result(invocation, raw)

runtime = CoreRunner()
runtime.register("manual", ManualRunner(my_dispatcher))
result = runtime.run(invocation_with_kind_manual)
```

## Installation

```bash
pip install core-runner
# or with HTTP support:
pip install "core-runner[http]"
```

For development:

```bash
git clone https://github.com/ProtocolWarden/CoreRunner.git
cd CoreRunner
pip install -e ".[dev,http]"
pytest -q
```

## Contracts

CoreRunner consumes RxP types directly:

```python
from rxp.contracts import RuntimeInvocation, RuntimeResult, ArtifactDescriptor
```

See [RxP](https://github.com/ProtocolWarden/RxP) for the contract definitions.

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE).
