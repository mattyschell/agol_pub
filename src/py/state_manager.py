#!/usr/bin/env python3
"""
State management for blue-to-green alternating deployments.

Usage:
  python state_manager.py init <state_file> [--start-color blue|green]
  python state_manager.py get-target <state_file>
  python state_manager.py set-success <state_file> <deployed_color>
  python state_manager.py set-failed <state_file>
  python state_manager.py get-state <state_file>
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def load_state(state_file):
    """Load state from file, or return None if not found."""
    if Path(state_file).exists():
        with open(state_file, 'r') as f:
            return json.load(f)
    return None


def save_state(state_file, state):
    """Save state to file."""
    Path(state_file).parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)


def init_state(state_file, start_color='blue', verbose=True):
    """Initialize state file."""
    state = {
        'current': start_color,
        'previous': 'green' if start_color == 'blue' else 'blue',
        'timestamp': datetime.now().isoformat(),
        'status': 'initialized'
    }
    save_state(state_file, state)
    if verbose:
        print(f"Initialized state: current={start_color}")


def get_target_color(state_file):
    """Get target color (opposite of current).

    Auto-initializes with current=blue on first run,
    so the first deployment targets green.
    """
    state = load_state(state_file)
    if not state:
        init_state(state_file, start_color='blue', verbose=False)
        state = load_state(state_file)

    current = state['current']
    target = 'green' if current == 'blue' else 'blue'
    print(target)
    return target


def set_success(state_file, deployed_color):
    """Mark deployment as successful; update current and previous."""
    state = load_state(state_file)
    if not state:
        print("ERROR: State file not found", file=sys.stderr)
        sys.exit(1)
    
    state['previous'] = state['current']
    state['current'] = deployed_color
    state['status'] = 'success'
    state['timestamp'] = datetime.now().isoformat()
    save_state(state_file, state)
    print(f"Success: {state['previous']} -> {deployed_color}")


def set_failed(state_file):
    """Mark deployment as failed."""
    state = load_state(state_file)
    if not state:
        print("ERROR: State file not found", file=sys.stderr)
        sys.exit(1)
    
    state['status'] = 'failed'
    state['timestamp'] = datetime.now().isoformat()
    save_state(state_file, state)
    print(f"Failed: current={state['current']}, previous={state['previous']}")


def get_state(state_file):
    """Print full state."""
    state = load_state(state_file)
    if not state:
        print("ERROR: State file not found", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(state, indent=2))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'init':
        state_file = sys.argv[2]
        start_color = sys.argv[4] if len(sys.argv) > 3 and sys.argv[3] == '--start-color' else 'blue'
        init_state(state_file, start_color)
    
    elif command == 'get-target':
        state_file = sys.argv[2]
        get_target_color(state_file)
    
    elif command == 'set-success':
        state_file = sys.argv[2]
        deployed_color = sys.argv[3]
        set_success(state_file, deployed_color)
    
    elif command == 'set-failed':
        state_file = sys.argv[2]
        set_failed(state_file)
    
    elif command == 'get-state':
        state_file = sys.argv[2]
        get_state(state_file)
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()