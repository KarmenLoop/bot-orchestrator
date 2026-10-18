#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run the MOA example shipped inside the standalone skill."""
from pathlib import Path
import runpy


if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[1] /
                      'skills/bot-orchestrator/scripts/moa_demo.py'), run_name='__main__')
