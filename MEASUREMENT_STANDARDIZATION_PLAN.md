# PIEC Measurement and Simulation Standardization Plan

Status: proposed design for review; implementation has not started.

## Implementation handoff: read this first

Implement **one numbered checkpoint from section 12 per task**. The architecture sections are requirements for those checkpoints, not permission to implement the whole document at once. Begin with checkpoint 1; do not start production changes during plan review.

For each checkpoint:

1. Read this plan, inspect `git status --short`, and identify the last completed checkpoint from Git history and the progress log below. Preserve unrelated uncommitted work, including the existing `processed` addition in the developer guide.
2. State the checkpoint number, files in scope, and acceptance tests. Read the relevant existing code and characterization fixtures before editing.
3. Implement only that checkpoint and its tests. Do not introduce dependencies on later checkpoints. Framework checkpoints use fake hooks/in-memory persistence until the real adapter exists.
4. Run focused acceptance tests and the full available suite. Report exact commands and results. A missing interpreter, skipped platform test, or unavailable hardware is a blocked/unverified gate, never a pass.
5. Review the diff for compatibility and unrelated edits. Update the progress log with results and remaining gates. Stage explicit paths, never `git add .`.
6. When checks pass, create the checkpoint commit if committing has been authorized. Otherwise stop with the exact diff ready to commit. Report commit hash (or uncommitted status), tests, remaining gates, and the next checkpoint. **Stop here; wait for the next task before continuing.** Do not squash checkpoints together.

If a numbered checkpoint is too large for one reviewable change, divide it into lettered commits using the split rules in section 12. Each lettered commit is also a stopping point. If a contract contradiction requires a design decision, describe it and amend the plan in a documentation checkpoint before dependent implementation.

Suggested implementation prompt:

> Read MEASUREMENT_STANDARDIZATION_PLAN.md. Implement only checkpoint <number or letter>, preserving existing uncommitted work. Follow the handoff checklist, run the stated checks, and stop at that checkpoint. Do not implement later stages. Report any gate you cannot verify. [Add "Commit the checkpoint when its automated checks pass" if desired.]

### Progress log

| Checkpoint | Status | Validation / remaining gates |
|---|---|---|
| Plan review | Revised, uncommitted | Source review on 2026-09-08; both baseline commits exist. Local pytest launch denied access to `.venv\\Scripts\\python.exe`; current test count unverified. |
| 1 onward | Not started | Record each completed checkpoint here; Git history supplies commit hashes. |

This document is the implementation contract for standardizing PIEC measurements. If a later implementation choice conflicts with this plan, the implementation must stop and the plan must be amended in a separate documentation commit before code continues.

## 1. Purpose and non-negotiable constraints

The goal is one recognizable measurement framework for DC I-V, MOKE, ferroelectric waveform measurements, and AMR/magneto-transport, while preserving the working public surface of each measurement.

The following constraints apply to every stage:

- Migration is incremental. There is no repository-wide rewrite.
- Existing class names, import paths, positional argument meanings, public compatibility methods, data columns, metadata/data CSV layout, and analysis results remain compatible unless an exception is explicitly approved and tested.
- New constructor and run options are keyword-only. Existing positional arguments never acquire a new meaning.
- Constructors perform no instrument I/O, including `idn()` calls.
- A measurement coordinates a procedure; an instrument driver implements its Level 2 instrument contract; a setup adapter owns lab-specific wiring, calibration, and safe-state policy; a physics model owns simulated sample behavior; a GUI owns presentation only.
- A measurement safe-state operation de-energizes or halts the configured setup but never disconnects instruments.
- The normal worker is the sole writer to instruments during an active run. GUI callbacks never compete with it.
- Generic DAQ and virtual-DAQ behavior is outside this migration unless an independently demonstrated DAQ contract defect requires a separate change. MOKE behavior never belongs in `VirtualDaq`.
- There is one physical `MokeMeasurement`; virtual operation is achieved by injecting virtual instruments and a simulated material/bench.
- Python 3.9 remains supported. The design does not rely on `ExceptionGroup` or other newer-only behavior.
- Software safing is best effort and conditional on a live Python process, a functioning communication path, and drivers that enforce finite I/O timeouts. It is not a substitute for a physical interlock or emergency disconnect.

## 2. Immutable baselines and compatibility contract

### 2.1 Baseline commits

Characterization is pinned to immutable commits, not a moving branch name:

| Scope | Baseline commit |
|---|---|
| Measurements present on `master` | `9d9760242f44a79401626964f0122cc91b149c18` |
| First complete MOKE implementation on this feature branch | `d1bac1ccf37e6578586336278c1ea36cf39b472` |

An earlier review reported 276 passing tests. This is a historical claim, not a verified gate: the 2026-09-08 review could not launch the local virtual-environment interpreter (access denied). Re-run and record the actual count/environment before implementation. Even a passing suite does not validate the proposed architecture because the shared base has not yet been implemented.

### 2.2 Compatibility manifest

Before production code changes, create a machine-readable manifest and characterization tests. For every public measurement, record:

- module and re-export paths;
- exact class name;
- constructor parameter order, names, defaults, and accepted legacy spelling;
- `run_experiment()` calls that existing notebooks and GUIs make;
- other public methods, their signatures, return behavior, and side effects;
- public attributes consumed by GUIs, notebooks, and analysis;
- snapshot types, properties, and column order;
- raw and processed data columns, order, and dtypes;
- metadata fields and the one-row metadata/blank-line/data CSV structure;
- filename grammar and associated plot artifacts;
- pause, abort, repeat-run, and virtual-instrument behavior.

Minimum public surfaces to characterize are:

| Family | Required compatibility coverage |
|---|---|
| `IVSweep` | Constructor; `configure_sourcemeter`, `sweep`, `save_data`, `run_experiment`; `data`, `metadata`, `filename` |
| `DiscreteWaveform` | Constructor; `initialize_awg`, `configure_oscilloscope`, `configure_awg`, `apply_and_capture_waveform`, `save_waveform`, `analyze`, `run_experiment`; `history`, `notes`, `filename` |
| `HysteresisLoop` | Constructor options including plotting and time shifting; processed CSV; `_PV.png`, `_IV.png`, and `_trace.png` artifacts |
| `ThreePulsePund` | Constructor and pulse parameters; processed PUND columns; `_dPvst.png` and `_trace.png` artifacts |
| `MagnetoTransport` / `AMR` | Legacy `arduino` and misspelled `voltage_callibration`; `initialize`, `set_field`, `configure_lockin`, `capture_data`, `capture_data_point`, `save_data_point`, `shut_off`, and `run_experiment(configure_lockin=True)`; pause/abort behavior |
| `MokeMeasurement` | Constructor including the `safe_shutdown=` callback; configuration and setpoint helpers; `shut_off`; `run_experiment(on_update=None, save=True)`; dynamic unit columns |
| `MokeSnapshot` | `.raw`, `.last_cycle`, `.cycle_average`, `.completed_cycles`, and `.field_column` |
| `piec.measurement.amr` | Re-exports of `MagnetoTransport`, `AMR`, `convert_angle_to_steps`, `convert_steps_to_angle`, and `convert_field_to_voltage` |

Compatibility tests use `inspect.signature`, unchanged call examples copied from repository notebooks and GUIs, golden CSV fixtures, numerical tolerances, and expected plot artifacts. Merely satisfying a `Protocol` is insufficient.

### 2.3 What is and is not frozen

The migration preserves call compatibility, not every unsafe implementation detail.

- Existing positional calls keep their meaning.
- Existing defaults stay the same unless retaining one would energize hardware unexpectedly; such a safety correction requires its own commit and release note.
- Common optional keywords such as `on_update`, `save`, and `save_partial` may be appended without invalidating old calls.
- Legacy measurement-specific `run_experiment` arguments remain accepted. In particular, AMR's first positional `configure_lockin` argument must never be reinterpreted as a callback.
- Old public methods remain thin compatibility adapters when internal hooks change.
- Existing column names and order remain exact during migration.
- Existing filename grammar remains the default. The persistence layer makes publication safe without silently changing users' naming scheme.
- Unsafe omissions such as failure to disable an output are explicitly not frozen.
- Intentional API or schema breaks require a new API/schema version, a converter or adapter, a migration note, and separate approval. No such removal is planned in this stack.

The following are explicit proposed compatibility exceptions; checkpoint 1 freezes them and checkpoint 2 records before/after expectations. Do not demand that golden fixtures reproduce the unsafe behavior:

- Instrument identity metadata is populated at configuration rather than construction. Constructors also stop creating output directories or reserving filenames (AMR currently calls `create_measurement_filename`).
- AMR's incremental writes move from a completed-looking CSV to a run-owned partial artifact. `filename` becomes available only after final publication; `partial_filename` exposes incomplete persistence. Document this attribute-timing change.
- Energizing standalone setters require an owner session; out-of-session calls raise before I/O with a migration example. In particular, AMR `initialize()`/`set_field()` and MOKE `set_output()`/`set_field()` cannot leave energized hardware outside a cleanup boundary.
- Existing `run_experiment()` return values remain unchanged: IV, FE, and AMR return `None`; MOKE returns its DataFrame. The common execution API returns data; legacy adapters explicitly translate that result. Preserve standalone helper returns too.
- Existing metadata keys/values remain where meaningful, with identity timing as above; new schema/run fields are additive. Golden comparisons normalize timestamps, run IDs, filenames, and instrument representations explicitly, without ignoring data or scientific parameters.

## 3. Target architecture

### 3.1 Layers and ownership

The standardized path is:

```text
GUI / notebook / automation runner
              |
       MeasurementRunner
              |
   concrete measurement adapter
              |
       BaseMeasurement
              |
 setup-role adapters and calibrations
              |
      Level 2 instrument drivers
```

Simulation replaces only the bottom two layers with a `VirtualBench`, virtual instruments, and injected physics models. It does not replace the measurement.

### 3.2 Common consumer contract

The GUI-facing protocol contains only operations that every migrated measurement can support:

- reserve a run synchronously;
- execute a previously reserved run with common run options;
- request cooperative stop;
- read `run_state`, `safety_status`, and a bounded snapshot;
- inspect the immutable last-run record.

`MeasurementRunner` owns the reservation-plus-thread-start sequence for GUIs. It does not contain measurement science or issue instrument commands.

Before reservation, the caller builds an immutable run request containing the common callback/save policy plus any validated measurement-specific compatibility option. Both synchronous legacy adapters and the GUI runner execute that same request, so AMR's `configure_lockin` option cannot leak through mutable instance state or change meaning between the two paths.

### 3.3 Base lifecycle versus legacy public methods

One inherited lifecycle implementation must coexist with unlike legacy signatures. Therefore:

- `BaseMeasurement` is the sole implementation of reservation, execution ordering, cancellation, safing, finalization, event delivery, and persistence dispatch.
- A concrete `run_experiment()` may remain as a thin signature-preserving adapter. It translates legacy arguments into common run options and immediately delegates to the base lifecycle; it may not reproduce lifecycle logic.
- Every migrated `run_experiment()` accepts the common optional keywords, while AMR also preserves `configure_lockin=True` in its original positional slot.
- `configure_instruments()`, `capture_data()`, `session()`, `safe_shutdown()`, and `request_stop()` are base-owned public wrappers after migration.
- Concrete measurements implement protected hooks: configuration, capture, analysis, metadata construction, bounded snapshot views, and setup-specific shutdown actions.
- Measurement-specific compatibility helpers such as `sweep()`, `apply_and_capture_waveform()`, `configure_sourcemeter()`, and `shut_off()` delegate to those wrappers or hooks without opening a second lifecycle path.
- Migrated subclasses are checked to ensure they do not override base-owned wrappers. Static `final` annotations and contract tests are required; a runtime subclass ban is deferred until external subclass compatibility is understood.

Keep MOKE's existing `capture_data(on_update=None)` positional call valid in the base-owned capture wrapper. Do not make its callback keyword-only retroactively. New capture options are keyword-only. Constructor `safe_shutdown=` remains accepted but the old callback-valued attribute is replaced by the lifecycle method; record this intentional attribute change in the manifest.

This resolves the signature conflict without weakening the single lifecycle owner.

### 3.4 Constructor and metadata rule

The base constructor initializes universal in-memory state only. Concrete constructors bind instruments and validate static parameters. They must not call overridable hooks or touch hardware.

Instrument identities and other live facts are collected during configuration, when the run is already inside a safety boundary. Static metadata can be prepared after all subclass fields exist.

### 3.5 Run record versus legacy history

Do not silently repurpose existing `history` attributes. Add an immutable common `RunRecord` and `run_records`; maintain legacy `history` behavior where consumers depend on its current contents.

A run record contains at least:

- full run ID and reservation generation;
- start/end timestamps;
- final state and outcome;
- save policy and final/partial artifact paths;
- last snapshot sequence;
- safety report;
- primary error phase, type, and message;
- cleanup, persistence, callback, and history-reporting errors;
- the exact schema name/version used.

Exception objects and tracebacks remain in memory only. Persisted metadata contains safe scalar summaries.

## 4. Run lifecycle and concurrency contract

### 4.1 States

Use these states consistently:

| State | Meaning |
|---|---|
| `IDLE` | No run has been reserved |
| `STARTING` | A run is reserved but its worker may not have begun |
| `CONFIGURING` | Instrument setup is in progress; outputs must remain disabled |
| `RUNNING` | Acquisition may energize the setup |
| `STOPPING` | Cancellation is latched and acquisition is yielding to safing |
| `SAFING` | Required shutdown actions are being attempted |
| `ANALYZING` | Hardware has been safed; successful raw data is analyzed |
| `SAVING` | A final artifact or incomplete-run artifact is being staged/published |
| `COMPLETED` | All requested success-path work finished |
| `ABORTED` | Stop won, safing succeeded, and required partial persistence succeeded |
| `FAILED` | A required operation failed |

The only legal forward transitions are:

| From | To |
|---|---|
| `IDLE`, `COMPLETED`, `ABORTED`, `FAILED` | `STARTING` for a newly reserved generation |
| `STARTING` | `CONFIGURING`, `STOPPING`, or `FAILED` if worker launch fails |
| `CONFIGURING` | `RUNNING`, `STOPPING`, or `SAFING` after an error |
| `RUNNING` | `STOPPING` or `SAFING` |
| `STOPPING` | `SAFING`, or `ABORTED` directly when no I/O began |
| `SAFING` | `ANALYZING` on a clean completed capture, `SAVING` for requested incomplete persistence, or a terminal state |
| `ANALYZING` | `SAVING`, `COMPLETED` when saving was not requested, or `FAILED` when no incomplete save is requested after an error |
| `SAVING` | `COMPLETED`, `ABORTED`, or `FAILED` according to the recorded outcome |

No other transition is permitted. State changes use one validation helper so measurement subclasses and GUIs cannot assign states directly.

Safety is separate from run state:

| Safety status | Meaning |
|---|---|
| `UNKNOWN` | No conclusion is available yet |
| `NOT_NEEDED` | The run ended before any instrument I/O could occur, or the setup has no hazardous action |
| `SAFING` | Shutdown attempts are in progress |
| `SAFE` | Every required software shutdown action reported success |
| `UNSAFE` | At least one required shutdown action failed or could not be confirmed |

Thread termination never implies `SAFE`. A shutdown report also records whether the safe state was command-only or independently read back; `SAFE` is not a claim that software physically measured zero field/current when the setup has no such readback.

### 4.2 Run reservation closes the Stop/start race

The GUI reserves synchronously before starting a worker. Reservation, under the state lock, must:

1. accept only `IDLE` or a terminal state;
2. reject a nested or concurrent run;
3. clear the stop event;
4. create a full 128-bit UUID and monotonically increasing local generation;
5. set `STARTING`;
6. return an opaque token bound to that generation.

Only after reservation does the GUI start a non-daemon worker with the token. The worker validates the token before I/O. A stale worker can never execute a newer reservation.

If Stop is pressed after reservation but before the worker starts, `request_stop()` latches the event while state is `STARTING`; the worker produces an aborted terminal record without touching hardware. If thread creation itself fails, the runner finalizes that reservation as `FAILED` with safety `NOT_NEEDED`.

A synchronous `run_experiment()` performs the same reserve-then-execute sequence internally.

### 4.3 Legal stop behavior

`request_stop()` and AMR's pause request are the only cross-thread control writes; reservation and copy-only state/snapshot reads are also supported. No such operation writes hardware. Stop's state behavior is:

| Current state | Result |
|---|---|
| `STARTING`, `CONFIGURING`, `RUNNING` | Set the event and transition to `STOPPING` |
| `STOPPING` | Leave state unchanged; request is idempotent |
| `SAFING`, `ANALYZING`, `SAVING` | Leave state unchanged; do not move backward |
| `IDLE` or terminal | Ignore the request |

The stop event is cleared only by a successful new reservation. The state lock is never held across instrument I/O, callbacks, waits, analysis, or disk access.

Preserve `abort_requested` as a compatibility property: assigning `True` requests stop; assigning `False` cannot clear an active run's stop event. Preserve AMR `pause_requested` through a thread-safe property/event and add `request_pause(paused=True)`. Pause retains the configured field as legacy behavior, takes effect at a documented acquisition boundary, and uses cancellable waits; Stop always wakes a paused worker. Reset pause on reservation. Test the unchanged assignments used by `Measurements/AMR/amr_GUI.py`.

Reservation also rejects while an idle `safe_shutdown()` owns the command lease. Acquire/release that lease under the same lock as run reservation, without holding the lock across I/O. Otherwise a new run can race with idle shutdown. Reject duplicate execution of the same token, not just stale generations. Reset current-run data, errors, and filenames at reservation so Stop-before-start cannot return a previous run's data; prior results remain in prior run records.

Acquisition delays use cancellable waits. Shutdown delays use a separate non-cancellable pacing function; a latched Stop must not collapse a safe ramp's required delay.

When capture returns, the worker takes the state lock to establish a completion linearization point. If Stop obtained the lock first, the outcome is aborted. If capture completion obtained it first, a later Stop does not convert completed acquisition into an abort.

### 4.4 Canonical full-run ordering

Every full run follows this order:

1. Reserve and enter `STARTING`.
2. If Stop is already latched, finalize as aborted without I/O.
3. Enter `CONFIGURING` and configure instruments with outputs disabled.
4. Atomically choose `RUNNING` or `STOPPING` based on cancellation.
5. Capture data. A callback failure is an acquisition failure.
6. Enter `SAFING` immediately after configuration/acquisition finishes or raises.
7. Attempt every required shutdown action and emit an immediate safety alert if any required action fails.
8. Only when acquisition completed and safing succeeded, enter `ANALYZING` and analyze an untouched copy/staging representation of raw data.
9. If saving was requested, enter `SAVING` and publish the final artifact atomically. Otherwise record `save_requested=false` and leave the final filename unset.
10. On abort or failure, skip scientific analysis and optionally stage an explicitly incomplete raw artifact according to the save policy.
11. Record diagnostics/history, choose exactly one terminal state, and emit exactly one terminal event.
12. Re-raise the selected error, if any, only after safing and finalization attempts finish.

`COMPLETED` is never assigned before required analysis and saving succeed.

### 4.5 Notebook and standalone operations

Piecewise notebook use is supported without creating multiple cleanup owners:

- `with measurement.session():` creates one reservation, records the calling thread as owner, and owns exactly one shutdown boundary on exit.
- Within that session, public configure/capture wrappers recognize the owner and do not create nested scopes.
- Nested sessions and `run_experiment()` inside a session are rejected.
- Cross-thread hardware-bearing calls are rejected.
- A session supports one capture operation; repeated acquisition belongs inside the concrete capture hook or in separate sessions.
- After a capture, clean session exit safes first and then runs analysis; it saves only when the session was explicitly given `save=True`. A configuration-only session has no analysis step.
- A successful configuration hook must leave outputs disabled and motion stopped.
- Standalone `configure_instruments()` uses a transient operation scope. On partial configuration failure it attempts safing before re-raising; on success its disabled-output postcondition is verified where the adapter supports readback.
- Standalone `capture_data()` uses a transient capture scope and always attempts safing. Inside a run/session it delegates without a second cleanup.
- Each standalone scope reserves and finalizes its own generation, emits one terminal event, and preserves the method's legacy semantics: it does not implicitly analyze or save.
- Direct calls to raw instrument objects are outside this guarantee and must be documented as such.

AMR is an explicit exception to the standalone no-save sentence above: legacy `capture_data()` performs incremental persistence. Its wrapper requests partial checkpoints by default and publishes the final CSV only after clean capture and safing, with no implicit analysis. `save_data_point()` inside that scope writes the current run's partial checkpoint; it never publishes completion. Full runs honor their explicit `save`/`save_partial` policy. A manual single-point workflow uses `with measurement.session(save=True):` and the point helper under that owner. Checkpoint 24 must test these call paths and document the filename-timing exception.

Configuration-only scopes transition from `CONFIGURING` through `SAFING` to `COMPLETED`; capture-only scopes also pass through `CONFIGURING` for prerequisite validation without silently repeating legacy configuration. The successful standalone configuration path uses the same cleanup boundary. Retain validated settings for subsequent capture (including MOKE's configured readiness), while marking outputs disabled. Owner tracking covers every public hardware helper, not just the four base wrappers.

### 4.6 Outcome and persistence matrix

Default `save_partial` follows `save`: no files are written when `save=False` unless the caller explicitly requests partial persistence.

The matrix describes the common execution result. Legacy `run_experiment()` adapters retain the return mapping in section 2.3. Every partial-save entry, including shutdown and final-publication failures, is conditional on `save_partial` and available raw rows. `save=False` also suppresses plot-file writes even when legacy `save_plots=True`; it does not suppress in-memory scientific analysis.

| Event | Analysis | Artifact policy | Final state | Caller receives |
|---|---|---|---|---|
| Clean success, `save=True` | Run | Publish completed CSV | `COMPLETED` | Data |
| Clean success, `save=False` | Run | No file; `filename=None` | `COMPLETED` | Data |
| Cooperative Stop with rows | Skip | Publish `.partial.csv` if requested | `ABORTED` if save succeeds | Partial data |
| Stop before I/O | Skip | No data artifact | `ABORTED` | Empty/current data |
| Configuration failure | Skip | No data file by default; diagnostics remain in the run record/event | `FAILED` | Original error |
| Acquisition/callback failure | Skip | Publish raw `.partial.csv` if requested | `FAILED` | Original error |
| Shutdown failure | Skip | Attempt raw `.partial.csv`; alert immediately | `FAILED` | Earlier error, otherwise `HardwareSafetyError` |
| Analysis failure | Failed | Publish untouched raw `.partial.csv` if requested | `FAILED` | Analysis error |
| Final publication failure | Already ran | Attempt a separately named raw `.partial.csv` | `FAILED` | Publication error |
| Required partial save failure after Stop | Skip | Data remains in memory | `FAILED` | Persistence error |

`self.filename` refers only to a successfully published completed artifact. Add `partial_filename` for incomplete data. The terminal event carries both.

## 5. Safety, error precedence, and instrument ownership

### 5.1 Setup-specific safe policy

The base cannot assume every instrument has a voltage zero, an analog output, or a motor. It invokes a concrete/setup shutdown hook through an attempt recorder.

A safe policy declares ordered required actions such as bounded ramp to the setup's electrical safe value, output disable, or optional motor stop. Important rules are:

- electrical safe output and zero physical field are distinct concepts;
- calibration is applied exactly once;
- output disable is attempted even if ramping fails;
- shutdown never enables an output;
- shutdown never calls `close()` or disconnects a session;
- motor halt is used only when the driver/adapter advertises it;
- repeated shutdown attempts do not create an unsafe action, though repeated communication failures are still reported.

The legacy MOKE constructor's `safe_shutdown=` callback remains accepted and is stored as a shutdown handler rather than shadowing the lifecycle method. A normal return means that callback reported success; an exception means safety is unconfirmed. The default MOKE policy explicitly ramps the source to electrical zero and disables its output.

Legacy `shut_off()` remains available. While a run is active it requests cooperative stop; while idle it invokes the safe-state wrapper directly. It never starts a competing hardware-writer thread.

A non-owner call to public `safe_shutdown()` during an active run must not write hardware. It latches cooperative Stop and raises a `RuntimeError` stating that shutdown is deferred to the execution owner; it never reports the hardware as safe. The execution owner performs and reports the actual shutdown. When no run is active, the caller may execute `safe_shutdown()` synchronously as the temporary command owner.

### 5.2 Shutdown timing requirements

Every energizing setup policy defines:

- finite source/read/query timeouts configured before energizing;
- a positive maximum output step;
- a finite ramp delay independent of cancellation;
- a total expected shutdown deadline;
- a final disable attempt even after a ramp error;
- setup-specific manual interlock instructions for the GUI.

The deadline is diagnostic, not magical preemption: Python cannot interrupt a native driver call that ignores its timeout. Hardware validation therefore includes timeout behavior and a physical emergency procedure.

### 5.3 Python 3.9-compatible failure handling

Cleanup attempts catch `BaseException`, record the failure, and continue through all required actions. If `KeyboardInterrupt` or `SystemExit` is the first primary event, it is deferred until those attempts finish and then re-raised unchanged. If one occurs later inside cleanup after an earlier primary error, it is recorded as a secondary cleanup failure and the earlier primary keeps precedence.

The engine records the first primary failure as exception, original traceback, and phase. It does not mutate `__context__` and does not use `ExceptionGroup`.

Error precedence is deterministic:

1. A configuration, acquisition, callback, analysis, or final-save error remains the primary error and is re-raised with its original traceback.
2. All cleanup and secondary persistence failures remain prominent in the safety report, last-run record, terminal event, and logs; they do not mask that primary error.
3. If ordinary cleanup fails without an earlier primary error, raise `HardwareSafetyError` containing the full shutdown report. A cleanup-only `KeyboardInterrupt` or `SystemExit` is instead re-raised unchanged after the remaining actions are attempted.
4. If a cooperative abort is otherwise clean but a required partial save fails, the run becomes `FAILED` and raises the persistence error.
5. A run-record/event reporting failure is recorded when possible and never replaces an earlier scientific or safety error.

The shutdown report lists every required action, whether it was attempted, whether it succeeded, its duration, any error, and whether independent readback was available. `SAFE` requires success of all required software actions; “thread ended” is insufficient, and “command sent” is distinguishable from a readback-verified state.

### 5.4 Connection ownership

Measurements never close instruments. Connection teardown belongs to whoever created the instrument:

- notebook/user-injected instruments remain open until the user closes them;
- a GUI closes only instruments it created;
- GUI-owned instruments are closed only after the worker is dead, the terminal event has arrived, and safety is `SAFE` or `NOT_NEEDED`;
- if safety is `UNSAFE` or unknown, the GUI preserves the warning and manual-interlock instructions. A forced exit requires explicit acknowledgement and must not be described as safe.

## 6. Snapshots, events, and GUI contract

### 6.1 Snapshot model

A common snapshot contains:

- run ID, monotonically increasing sequence, state, completed steps, and optional total steps;
- a status message;
- fresh bounded DataFrame views such as `raw_window`, `last_cycle`, or `cycle_average`.

A frozen dataclass alone does not make DataFrames immutable, so every exposed view is a copy. Acquisition stores rows efficiently and must not rebuild/copy the full DataFrame for every point. Full data is materialized only at bounded checkpoints, cycle boundaries, or completion as appropriate.

MOKE preserves its existing snapshot properties as aliases/views while also exposing the generic mapping.

MOKE `.raw` is already the bounded `raw_window_points` window, not the full dataset. Preserve that meaning and the existing last-cycle/average shapes. Copy views under a short snapshot-publication lock; do not iterate buffers while another thread mutates them. Terminal snapshots remain bounded; full raw data is available separately after completion.

### 6.2 Two event paths

Use two distinct paths:

- a bounded, coalescing display queue for high-rate snapshots; dropping an older display snapshot is allowed;
- an unbounded/non-droppable control path for state changes, safety alerts, and one terminal event.

The terminal event contains the final deep-copied snapshot, outcome/state, safety report, final and partial filenames, primary error summary, and secondary failures. Including the authoritative final snapshot prevents a terminal event from overtaking the final display state.

### 6.3 GUI threading and close behavior

All measurement GUIs continue to use the repository's `MeasurementApp` styling and layout conventions. Standardization changes worker behavior, not the visual language.

Rules:

- no Tk or Matplotlib widget call occurs from the worker;
- no GUI callback issues an instrument command while a run is active;
- workers are non-daemon;
- Run reserves synchronously before thread start;
- Stop only calls `request_stop()`;
- window close sets a closing flag, requests stop, disables controls, and continues polling through `after()`;
- Tk callbacks never block on `join()`;
- the window closes only after worker termination, terminal delivery, and confirmed safety;
- queue saturation cannot discard terminal or safety information;
- exceeding the expected stop deadline displays the setup's physical-interlock procedure but never launches a second writer;
- GUI Stop is labeled/described as cooperative software stop, not a physical emergency stop.

FE `show_plots` and AMR `live_plot`/`plot_results` remain accepted compatibility options. Synchronous main-thread notebook calls may render through presentation helpers. Runner execution must never invoke interactive pyplot, Tk, `show()`, or canvas updates; deliver plot data to the UI instead. Saved plot artifacts use noninteractive figures and retain legacy names. Test both execution paths; do not silently drop notebook plotting.

## 7. Versioned data and units contract

### 7.1 Schema metadata

Every saved run adds scalar metadata fields:

- `measurement_schema`;
- `measurement_schema_version`;
- `run_id`;
- `outcome` (`completed`, `aborted`, or `failed`);
- `partial`;
- `save_requested`;
- canonical `column_units_json`.

The units value is a JSON string with sorted keys and compact separators. It contains every data column exactly once; values are canonical unit strings, with JSON `null` for categorical/index columns that have no physical unit. `json.loads()` must reproduce the exact mapping after a CSV round trip. A Python dictionary stored directly in a DataFrame cell, `DataFrame.attrs`, or a docstring alone is not a persistence contract.

For flat CSV data, new measurements follow the repository's existing self-describing `quantity (unit)` convention unless a future file-format version explicitly changes it. Existing names are not normalized to snake case during this migration.

Commanded, calibrated, and measured quantities remain separate columns. In particular, a calibrated field inferred from source output is not renamed as a measured gaussmeter field.

### 7.2 Exact legacy column contracts

| Family | Columns preserved in order |
|---|---|
| `IVSweep` | `voltage (V)`, `current (A)` |
| `AMR` | `angle`, `field`, `X`, `Y` |
| MOKE raw/final | `time (s)`, `cycle`, `point`, `direction`, dynamic `source_output ({output_unit})`, dynamic `field_calibrated ({field_unit})`, `detector_voltage (V)`, then optional `field_measured ({field_unit})`, `field_time (s)` |
| Hysteresis raw | `time (s)`, `voltage (V)` |
| Hysteresis processed | Raw columns plus `current (A)`, `polarization (uC/cm^2)`, `applied voltage (V)` |
| Three-pulse PUND raw | `time (s)`, `voltage (V)` |
| Three-pulse PUND processed | Raw columns plus `current (A)`, `polarization (uC/cm^2)`, `P^ (uC/cm^2)`, `P* (uC/cm^2)`, `P^r (uC/cm^2)`, `P*r (uC/cm^2)`, `dP (uC/cm^2)`, `applied voltage (V)` |

The Phase 0 manifest settles exact dtypes and snapshot-view ordering from the pinned baselines. A renamed/removed column or changed physical meaning requires a new schema version and converter.

### 7.3 Raw versus processed data

Raw acquisition records are preserved independently from analysis output. Analysis receives an in-memory copy or an unpublished staging representation. A partially mutated analysis result can never replace the recoverable raw data.

For FE/PUND, file-oriented analysis is converted to pure DataFrame functions before the measurement migration. Legacy path-based functions remain as wrappers and must produce numerically equivalent results.

## 8. Windows- and SMB-aware persistence

PIEC guarantees that it never intentionally presents a partially written completed `.csv`. It does not claim universal power-loss durability or universal atomic rename semantics on every SMB server.

### 8.1 Write and publish rules

1. Generate a full UUID for the run and use it in staging/checkpoint ownership.
2. Create staging files in the destination directory with `tempfile.mkstemp()`; do not hold an open `NamedTemporaryFile` across rename on Windows.
3. Write metadata, the blank separator, and data through one UTF-8 text handle. Flush and `fsync` that handle, then close it before publication.
4. Add a handle-based writer. Preserve the legacy path-based helper as a compatibility wrapper; do not compose an atomic write from the current helper's three independent opens.
5. Preserve each measurement family's legacy final filename grammar. Claim a candidate with an exclusively created hidden marker at a deterministic path derived from the candidate basename; store the full owner UUID inside it. A UUID in the marker filename alone would let competing writers reserve the same candidate. On collision choose the next legacy index. Never reserve by creating an empty completed-looking CSV. A stale marker is not reusable until the explicit age/ownership recovery policy approves it.
6. Publish through one tested `atomic_publish_no_replace` abstraction. It must reject an existing target and never silently overwrite it. `Path.replace()` is not a no-replace operation.
7. Where a filesystem cannot provide the required no-replace primitive, strict mode fails clearly and leaves data in memory/staging. Any opt-in weaker mode must be labeled collision-resistant, never collision-proof.
8. Assign `self.filename` only after the completed CSV is published successfully.
9. Readers ignore `.partial` and staging files.

### 8.2 Multi-artifact measurements

For measurements that create plots:

- reserve one legacy-compatible basename for the artifact bundle;
- stage every expected artifact with run-owned UUID names;
- publish side artifacts first and the completed CSV last, using the CSV as the completion marker;
- never overwrite an existing side artifact;
- on failure, remove only artifacts proven to belong to the current reservation and record any orphan cleanup failure.

Cross-file publication is not claimed to be transactional. Publishing the CSV last ensures normal PIEC readers do not treat an incomplete bundle as complete.

### 8.3 Partial data and recovery

- In-progress checkpoints and terminal incomplete data use a full-run-ID `.partial.csv` name and never look like completed output.
- Replacing the checkpoint owned by the same run is an intentional overwrite and is separate from first publication.
- Abort/failure leaves `self.filename=None` and records `partial_filename`.
- On a save error, in-memory data remains available and recoverable staging paths are reported.
- Stale partial/reservation cleanup is explicit, ownership-checked, and age-gated; it never deletes an unknown file automatically.

### 8.4 Persistence tests

Tests cover:

- simultaneous writers selecting the same legacy candidate;
- pre-existing final and side-artifact targets;
- failures during metadata, data, flush, sync, close, and publication;
- non-ASCII metadata and JSON unit round trips;
- interrupted checkpoints and stale reservations;
- cleanup ownership;
- local NTFS behavior;
- the lab SMB path only when explicitly configured.

SMB results are recorded for the tested server/filesystem and are not generalized to all network shares.

## 9. Driver and setup-adapter prerequisites

Measurement code must not infer contract parity from similar method names. Each advertised driver used by a slice receives a shared contract test before that measurement migrates.

### 9.1 Sourcemeter

Audit the applicable Level 2 source/sense surface, including output control, source/sense selection, source voltage/current, both compliance modes, voltage/current source configuration, quick read, and voltage/current/resistance getters.

`VirtualSourcemeter` must accept the same optional `channel=1` convention on every applicable method, including the safety-critical output-disable path. Single-channel behavior and old positional calls remain unchanged. Measurements pass driver arguments by explicit keyword.

### 9.2 DMM

Before the MOKE slice, contract-test voltage configuration and reading across every advertised DMM intended for that setup: sense-function selection, DC coupling, optional range/integration settings, `get_voltage()`, and finite/non-finite return handling. Unsupported optional configuration is capability-gated explicitly; it is not inferred by catching arbitrary driver errors. `VirtualDMM` must obey the same call and scalar-return contract.

### 9.3 AWG

Two independent base-driver defects require separate fixes and tests:

- un-indent `Awg.output_trigger()` so it is actually a class method;
- apply `trigger_source` when it is not `None` in `configure_trigger()`.

Then audit concrete AWGs for real manual-trigger support. Manual triggering is required only for measurements whose chosen synchronization mode needs it; otherwise it is capability-gated. Contract tests also verify waveform selection, amplitude, offset, frequency, trigger ordering, and disabling every used channel on every exit.

### 9.4 Oscilloscope

Existing `get_data()` signatures and returned column names differ. Measurements use a `WaveformReader` setup adapter that returns exactly `time (s)` and `voltage (V)` for a requested channel. The adapter maps driver-specific `Time`, `Voltage`, or `Voltage_CH{channel}` fields, validates finite numeric equal-length arrays, and records actual channel/sample information.

Do not add a fictitious `read_waveform()` requirement to every oscilloscope driver, and do not make scientific measurement code parse driver-specific tables.

### 9.5 AMR roles

AMR uses setup-local roles rather than pretending unrelated instruments are interchangeable:

- `FieldSource`: set a requested calibrated field and apply the configured electrical safe-output policy;
- optional `FieldReader`: read actual field with declared units;
- `SignalReader`: return a real X/Y pair;
- `Rotator`: move by requested angle with limits/residual-step handling and stop only if supported.

A DCCalibrator adapter maps to voltage output; a sourcemeter adapter maps to its source methods. Field calibration is applied exactly once. A scalar DMM reading cannot silently be labeled `X` and `Y`; supporting a DMM-only AMR signal is a future explicit schema/version decision.

The Stepper base guarantees only its existing step operation. Homing, position readback, and halt remain optional capabilities.

### 9.6 MOKE roles

The general MOKE measurement uses:

- a sourcemeter as the direct calibrated output source;
- a DMM as the detector-voltage reader;
- an injected calibration mapping direct source output to field;
- an optional gaussmeter/field-reader adapter whose measured field remains a separate column.

No lab-specific power amplifier or magnet behavior is embedded in the sourcemeter/DMM drivers. The setup adapter and calibration describe that wiring.

In-plane and out-of-plane GUI choices select validated setup profiles before the run. A profile binds the appropriate source/channel, calibration, limits, optional field reader, and shutdown policy while the same `MokeMeasurement` performs the loop. Geometry is saved as metadata. When measured-field plotting is enabled and a field reader is present, the GUI plots the measured-field column; otherwise it plots calibrated field, and both columns remain distinct in saved data.

## 10. Measurement vertical slices

### 10.1 DC I-V

Preserve the existing constructor, voltage/current columns, filename convention, `configure_sourcemeter()`, `sweep()`, `save_data()`, and no-argument `run_experiment()` call. Add the common optional run keywords.

Configuration leaves the source at electrical zero with output disabled. Capture performs bounded, cancellable ramping and reading. Safing ramps to zero using shutdown pacing and disables output. Fault-injection tests cover every source and read call.

### 10.2 MOKE

Preserve its constructor, calibration object behavior, dynamic columns, optional field readback, `shut_off()`, callback shape, and all existing snapshot properties. Internally rename the constructor callback so it cannot shadow the base lifecycle method.

Capture accumulates efficiently, publishes bounded raw/last-cycle/average snapshots, and distinguishes calibrated from measured field. The outer base lifecycle is the only cleanup owner.

### 10.3 Discrete waveform, hysteresis, and PUND

Preserve `DiscreteWaveform`, `HysteresisLoop`, and `ThreePulsePund`, their public configuration/save methods, exact raw/processed schemas, numerical results, and plot artifacts.

First introduce in-memory hysteresis and PUND analysis with legacy file wrappers. Then migrate acquisition through the waveform adapter and shared lifecycle. Safing disables all used AWG channels even when one disable command fails.

### 10.4 Magneto-transport and AMR

Preserve public class/re-export names, constructor positional meaning, `arduino`, `voltage_callibration`, `run_experiment(configure_lockin=True)`, pause/abort behavior, and `angle`, `field`, `X`, `Y`.

Move live plotting to the GUI without removing compatibility plotting helpers until their use is characterized. Remove instrument writes and identity queries from construction. Validate rotator, field-source, optional field-reader, and X/Y signal-reader roles separately before integration.

## 11. Simulation modernization

Simulation changes are additive and occur after measurement lifecycle migrations are stable.

### 11.1 Scope

Audit every consumer of shared virtual sample state:

- `VirtualInstrument` global `sample` / `mag_sample`;
- `VirtualDMM`;
- `VirtualSourcemeter`;
- `VirtualCalibrator`;
- `VirtualLockin`;
- `VirtualStepper`;
- `VirtualAwg`;
- `VirtualScope`;
- DAQ-to-AWG/scope adapters only if their own interface tests expose a defect.

### 11.2 Role-specific protocols and hooks

Use small roles for field-responsive materials, angle-dependent resistance, voltage/waveform response, and two-terminal electrical loads. The electrical-load contract supports voltage-source and current-source operation, compliance, time, and state; a one-way voltage-to-current callback is insufficient.

Virtual hooks are generic:

- DMM voltage reader;
- sourcemeter electrical load;
- per-channel scope reader;
- lock-in X/Y reader;
- calibrator field/output binding;
- stepper angle/material binding;
- AWG/scope signal routing.

Explicit per-instance injection takes precedence. Existing shared-sample behavior remains as a deprecated fallback until all internal and documented callers migrate or a major release removes it. No MOKE-, AMR-, or FE-specific branch is added to a generic virtual driver.

### 11.3 VirtualBench

`VirtualBench` owns material instances, virtual instruments, connection routing, reset, seed/RNG, and a deterministic timebase. Resetting one bench cannot mutate another. Tests run two benches concurrently, cover voltage- and current-source operation, verify compliance, and compare physical/virtual measurement schemas.

For MOKE simulation, the bench routes the sourcemeter's direct output through the injected field calibration to a hysteretic magnetic material, then exposes that material's optical response as a generic DMM voltage-reader hook; an optional second reader supplies simulated gaussmeter field. This wiring lives in the bench/setup fixture, never in `VirtualDMM`, `VirtualSourcemeter`, or the measurement class.

## 12. Commit-by-commit implementation stages

Every commit is independently testable and revertible. Tests for a behavior land in the same commit as that behavior, except characterization tests, which deliberately precede production changes. Do not combine framework refactoring with new scientific algorithms.

Global code-commit gate:

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider
```

CI also runs on Python 3.9 and the current supported Python. A commit is not called physically validated until the hardware record described below exists.

Verify the CI matrix exists; if it does not, add it as a separate checkpoint before claiming supported-version validation. Do not repair or replace the user's Python environment as part of a measurement refactor. An unavailable test runner blocks the code-commit gate until a working approved environment is available.

### File map and required splits

Use these module boundaries unless repository instructions require otherwise. Keep scientific code in its current module and preserve exports.

| Area | Files |
|---|---|
| New lifecycle/value types | `src/piec/measurement/base.py`, `contracts.py` |
| New worker/events | `src/piec/measurement/runner.py` |
| New persistence | `src/piec/measurement/persistence.py`; legacy wrapper in `src/piec/analysis/utilities.py` |
| New setup adapters | `src/piec/measurement/adapters/` |
| IV / MOKE | `src/piec/measurement/iv_sweep.py`, `moke.py` |
| FE / analysis | `src/piec/measurement/discrete_waveform.py`, `src/piec/analysis/hysteresis.py`, `pund.py` |
| AMR | `src/piec/measurement/magneto_transport.py`, `amr.py` |
| GUIs | `Measurements/DCIV/IV_sweep_GUI.py`, `Measurements/MOKE/MOKE_GUI.py`, `Measurements/Ferroelectric Testing/FE_testing_GUI.py`, `Measurements/AMR/amr_GUI.py` |
| New tests / fixtures | Focused `tests/test_measurement_*.py`, `tests/fixtures/measurement_compatibility/` |

Split these broad checkpoints into the following separately tested commits; keep the numbered subjects below as their overall scope:

- **2a–2d:** manifest/test harness, IV+MOKE fixtures, FE/PUND fixtures, AMR fixtures. Capture baselines in isolated temporary checkouts or extracted trees; do not switch or reset this dirty working tree. Never connect real hardware. Mark demonstrated baseline defects with narrow expected-failure tests and a linked repair checkpoint; a broken legacy pipeline is not a requirement to fabricate passing goldens. Generate scientific reference outputs with deterministic fixtures and the pinned analysis functions.
- **9a–9c:** full-run lifecycle with fake hooks and an injected persistence interface; notebook/standalone ownership; fault/error-precedence tests and hardening. A minimal in-memory record/event sink lands with 9a so finalization does not depend on checkpoint 10.
- **10a–10b:** bounded snapshots and control/display events; runner and launch/close coordination tests.
- **11a–11c:** handle writer/schema round trips; no-replace single-file publication and collisions; bundles/partials/recovery fault tests. Specify and test each supported filesystem primitive before connecting production measurements.
- **20a–20c:** migrate `DiscreteWaveform` acquisition; integrate hysteresis analysis/plots; integrate PUND analysis/plots. Each remains usable through legacy calls.
- **24a–24c:** transport ownership/roles and legacy controls; AMR capture/checkpoints; notebook presentation compatibility and integration. Do not leave a migrated public class with a broken full-run path between commits.
- **28a onward / 30a–30d:** one virtual-driver hook family or one measurement fixture family per commit, respectively.

At every split, the public measurement still runs through either its complete old path or its complete new path; never expose half a migration. If that requires an internal opt-in adapter until the final subcommit, keep it private and test both paths.

Hardware checkpoints 17/22/26 are manual release gates. Software-only work on subsequent families may proceed while those records are `PENDING`; physical use and claims of physical validation may not. Scientific additions in checkpoint 32 are **out of scope for this standardization implementation** unless separately requested; skip them and proceed to documentation.

### Stage 0 — Approve and freeze behavior

1. `docs(measurement): finalize standardization contract`
   - Commit this plan only.
   - Gate: human review confirms no unresolved contradictory requirement.

2. `test(measurement): characterize legacy public behavior`
   - Add the compatibility manifest, golden CSVs, signature/call tests, and plot-artifact tests for both pinned baselines.
   - Classify each difference as preserved behavior, additive API, or approved safety correction.
   - Gate: preserved behavior passes before any production refactor; narrowly documented pre-existing defects are explicitly expected failures, with repair checkpoints. No broad `xfail`/skip may conceal a regression.

### Stage 1 — Repair prerequisites and add the engine

3. `fix(awg): expose output_trigger on the base class`
   - Indentation fix plus focused contract test only.

4. `fix(awg): honor configured trigger source`
   - Conditional fix plus focused tests; audit affected concrete drivers.

5. `fix(virtual-sourcemeter): align optional channel signatures`
   - Cover every applicable method and output-disable path; add no sample-specific physics.

6. `test(dmm): verify the standard voltage-read contract`
   - Run one fake-transport contract suite against every DMM advertised for MOKE plus `VirtualDMM`; add production changes only in a separate fix commit if the audit finds a defect.

7. `feat(measurement-adapter): normalize oscilloscope waveforms`
   - Add the `WaveformReader` adapter and fake-driver contract tests without migrating a measurement.

8. `feat(measurement): add state reservation and run records`
   - Add states, safety status, full IDs/generations, locked reservation, cancellation rules, immutable run records, and state tests.
   - Gate: simultaneous-run rejection, Stop-before-worker-start, stale-token rejection, repeated runs, and legal transition tests.

9. `feat(measurement): add safe lifecycle and notebook sessions`
   - Add base execution, protected hooks, standalone wrappers, single-owner sessions, shutdown reports, and Python 3.9 error precedence.
   - Gate: inject faults in configuration, acquisition, callbacks, safing, `KeyboardInterrupt`, and `SystemExit`; verify all shutdown actions are attempted.

10. `feat(measurement): add snapshots events and gui runner`
   - Add bounded snapshots, separate display/control paths, synchronous reservation, and non-daemon runner tests.
   - Gate: queue saturation, terminal ordering, thread-start failure, and snapshot mutation isolation.

11. `feat(measurement): add atomic schema-aware persistence`
    - Add handle-based CSV writing, schema metadata, run-owned staging/partial files, strict no-replace publication, and bundle support while retaining the legacy helper.
    - Gate: NTFS concurrency/fault tests and opt-in SMB tests; never claim untested filesystem guarantees.

12. `docs(measurement): align the developer guide with the engine`
    - Replace the old boolean-abort and constructor-I/O template immediately after the base contract lands.
    - Document hooks, legacy adapters, sessions, ownership, snapshots, units, persistence, GUI threading, and hardware gates.
    - Gate: examples import/compile and do not show concurrent hardware writers.

### Stage 2 — Pilot measurements and GUIs

13. `refactor(iv): migrate IVSweep to the shared lifecycle`
    - Preserve old calls/schema and add cancellation/safing/snapshots.
    - Gate: compatibility goldens and fault injection at every source/read step.

14. `refactor(moke): migrate MokeMeasurement to the shared lifecycle`
    - Preserve calibration, optional gaussmeter, callbacks, columns, snapshots, and custom shutdown callback.
    - Gate: calibrated/measured modes, partial cycles, averages, callback faults, repeated runs, and final safe state.

15. `refactor(dciv-gui): use the shared measurement runner`
    - Preserve `MeasurementApp` style and controls; remove worker-side Tk access.
    - Gate: import without `mainloop`, Stop-before-start, close while active, terminal errors, and owned-instrument close.

16. `refactor(moke-gui): use the shared measurement runner`
    - Preserve geometry selection and raw/last-cycle/average views.
    - Gate: virtual run, coalescing snapshots, Stop/close, safety alert, and terminal delivery.

17. `test(hardware): record IV and MOKE pilot validation` — only after execution
    - Commit a dated validation record; leave this commit absent/PENDING until tests occur.

### Stage 3 — Ferroelectric vertical slice

18. `refactor(analysis): add in-memory hysteresis processing`
    - Keep the legacy file wrapper; prove numerical and column equivalence.

19. `refactor(analysis): add in-memory PUND processing`
    - Keep the legacy file wrapper; prove numerical and column equivalence.

20. `refactor(fe): migrate the discrete-waveform family`
    - Use the waveform adapter, preserve APIs/schemas/plots, and disable every used AWG channel on all exits.
    - Gate: trigger ordering, impedance/channel mapping, golden numerical output, and injected failures.

21. `refactor(fe-gui): use the shared measurement runner`
    - Preserve layout, settings, and virtual selection; keep all Tk/plot work on the UI thread.

22. `test(hardware): record FE validation` — only after execution
    - Commit a dated low-amplitude AWG/scope validation record; otherwise remain PENDING.

### Stage 4 — AMR vertical slice

23. `feat(amr): add explicit setup-role adapters`
    - Add field source/reader, X/Y signal reader, and rotator adapters with unit, limit, calibration-direction, and capability tests.

24. `refactor(amr): migrate MagnetoTransport and AMR`
    - Preserve legacy spellings, positional semantics, re-exports, schema, and pause behavior; remove constructor I/O and measurement-owned plotting.
    - Gate: role isolation, exact goldens, Stop during dwell/motion, and field/motion safety on every injected fault.

25. `refactor(amr-gui): use the shared measurement runner`
    - Preserve layout/settings and move live plotting fully to the UI thread.

26. `test(hardware): record AMR validation` — only after execution
    - Commit separate role tests followed by a dated low-field integrated result; otherwise remain PENDING.

### Stage 5 — Additive simulation modernization

27. `feat(simulation): add role-specific physics contracts`
    - Define units, reset, deterministic time/RNG ownership, and electrical-load behavior without moving old classes.

28. `feat(virtual): add generic per-instance sensing and load hooks`
    - Add backward-compatible hooks to the relevant virtual drivers; explicit injection wins over legacy global fallback.

29. `feat(simulation): add composable VirtualBench`
    - Add routing, ownership, reset isolation, deterministic time/noise, and two-bench concurrency tests.

30. `test(simulation): migrate measurement fixtures to VirtualBench`
    - Move MOKE, IV, FE/PUND, and AMR fixtures one family at a time while retaining legacy fallback tests.

31. `refactor(simulation): retire internal global-sample use`
    - Only after repository consumers have migrated. Keep the documented compatibility fallback until a separately approved major release.

### Stage 6 — Scientific additions and final documentation

32. Optional, separately requested: one commit per scientific algorithm
    - Coercivity, remanence, leakage compensation, or fitting each receives its own reference dataset, documented units, tolerance, and review.
    - These commits never alter raw acquisition.

33. `docs(measurement): publish workflows and migration notes`
    - Update measurement docs, examples/notebooks, package exports, Sphinx toctree, and changelog.
    - Gate: notebooks parse and run offline with virtual instruments; docs build; full suite passes.

## 13. Physical validation records

Automated/virtual tests do not prove physical safety. Each hardware checkpoint stays marked `PENDING` until a record contains:

- date and tester;
- exact instrument model, serial/asset identifier as appropriate, and firmware;
- wiring/load and measurement geometry;
- driver and repository commit;
- configured voltage/current/field/frequency limits and compliance;
- physical interlock and manual emergency procedure;
- commanded-versus-observed output/readback;
- Stop and window-close latency;
- injected/read timeout behavior;
- observed final output-enable state and residual output/field;
- pass/fail result and anomalies.

MOKE validation is staged: first source plus DMM into a benign electrical load and observed by an oscilloscope; only then the amplifier/magnet with established limits and interlock. AMR validates motion and field roles independently before combining them. FE begins at low amplitude into an explicitly known impedance.

## 14. Definition of done

The standardization is complete only when:

- the compatibility manifest passes for every family;
- every migrated public runner delegates to one base lifecycle;
- the Stop/start race, stale worker, callback failure, shutdown failure, and window-close cases are tested;
- every reserved run has one terminal record/event and a separately reported safety result;
- incomplete data cannot appear as a completed CSV and no publisher silently overwrites a target;
- exact legacy schemas and numerical regression fixtures pass;
- the developer guide matches the implemented contract;
- two virtual benches run concurrently without cross-talk;
- all automated tests pass on supported Python versions;
- physical checkpoints are recorded as passed or explicitly remain `PENDING`;
- no legacy API or global virtual fallback is removed without a separately approved deprecation cycle.
