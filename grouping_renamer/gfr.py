#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Rename files like <dir>/<prefix><ID><suffix>.<ext>
according to ordering file while retaining grouping.

Usage: see --help

NOTE: partly written to force me into learning some Python (3.11),
so apologies if coding sucks/is non-Pythonic (suggestions for improvement?)
"""

import typer

__author    = "Wayne Stidolph"
__email     = "wayne@stidolph.com"
__license   = "MIT License (see file LICENSE)"
__copyright = "Copyright Wayne Stidolph, 2023"
__status    = "Development"

main=typer.Typer() # for command processing

# launch topshell?