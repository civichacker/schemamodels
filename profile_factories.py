#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Root entry point for profiling SchemaModelFactory V1 vs V2.
"""

from profiling.profile_factories import run_profile

if __name__ == "__main__":
    run_profile()
