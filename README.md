# knoteboard

**knoteboard** is a small command-line personal ticket management tool that
provides a Kanban-style board.

Upstream at: https://github.com/rmind/knoteboard

## Introduction

The tool is intended to be very minimalistic, but fast to operate.  It may
be used for **sticky notes** with reminders or it may be used as a basic
**Kanban-style board**.  It supports **Vi-style key bindings**.

## Usage

Install and run:
```shell
pip install knoteboard
python -m knoteboard
```

From the repo:
```shell
uv run python -m knoteboard
```

Press the `?` key inside the application to get a full list of the available
actions.  Just follow the status bar where available actions (the key
bindings) are described.

You can use `KNOTEBOARD_PATH` environment variable or specify the first
command line argument to create separate boards or store data in a directory
other than your home directory.
