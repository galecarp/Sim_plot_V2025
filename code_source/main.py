#!/usr/bin/env python3.10

__copyright__ = """
    Test WindSolarEnergyAnalysis
    Copyright (C) 2024 Mufan
"""

__license__ = "TODO"

""" **The main entry point of the client application.**

This module is the main entry point for the client application. It deals with the
command-line parameters and starts an instance of ConfoClient accordingly.
"""

# import argparse
import sys
import os
import inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


def print_copyright_notice():  # pragma: no cover
    notice = \
        'Test WindSolarEnergyAnalysis'

    print(notice + '\n')


if __name__ == "__main__":
    print_copyright_notice()
