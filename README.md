# Gossip Membership Protocol (MP1)

This repository contains a C++ implementation scaffold for a gossip-style membership and failure detection protocol (MP1), along with scripts used to run local grading scenarios.

## Project Layout

- `MP1Node.cpp`, `MP1Node.h`: Membership protocol logic (join, heartbeat gossip, failure detection)
- `Application.cpp`, `Application.h`: Simulation driver
- `EmulNet.*`: Emulated network layer
- `Member.*`: Node state and membership list structures
- `Log.*`: Event logging helpers
- `Params.*`: Simulation parameters
- `testcases/*.conf`: Failure and message-drop scenarios
- `Grader.sh`: Local grader script
- `run.sh`: Script used to build and run all 3 scenarios and produce logs

## Prerequisites

For the C++ simulator:

- Linux/macOS shell
- `g++` with C++11 support
- `make`

Optional Python service files (`main.py`, `submit.py`) additionally require Python 3 and third-party packages.

## Build

```bash
make clean
make
```

This produces the executable:

- `./Application`

## Run Scenarios Manually

```bash
./Application testcases/singlefailure.conf
./Application testcases/multifailure.conf
./Application testcases/msgdropsinglefailure.conf
```

Each run writes simulation logs (for example `dbg.log`).

## Run Local Grader

```bash
bash Grader.sh
```

Verbose mode:

```bash
bash Grader.sh -v
```

The grader evaluates join behavior, completeness, and accuracy across scenarios.

## Run Batch Script (Produces dbg.0/1/2)

`run.sh` in this repository expects two arguments:

1. Working directory for temporary artifacts and output logs
2. Source directory containing this project

Example:

```bash
WORKDIR=/tmp/mp1-run
SRCDIR=$(pwd)
bash run.sh "$WORKDIR" "$SRCDIR"
```

On success it creates:

- `/tmp/mp1-run/dbg.0.log`
- `/tmp/mp1-run/dbg.1.log`
- `/tmp/mp1-run/dbg.2.log`

## Cleaning Artifacts

```bash
make clean
```

This removes object files, executable, and common generated logs.

## Notes for MP1 Implementation

- Most assignment logic belongs in `MP1Node.cpp`.
- Key constants are defined in `MP1Node.h`:
  - `TFAIL`
  - `TREMOVE`
  - `FANOUT`
- Useful events to verify in logs:
  - node join
  - node removal after timeout
  - heartbeat propagation

## Optional Python Submission API

This workspace also includes:

- `main.py`: FastAPI service that starts grading/submission jobs
- `submit.py`: Asynchronous Coursera submission helper

If you plan to use this path, install dependencies (example):

```bash
pip install fastapi uvicorn sqlalchemy aiosqlite python-dotenv httpx email-validator
```

Then provide environment variables (such as `DATABASE_URL`) before starting the API.
