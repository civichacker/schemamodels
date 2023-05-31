# SPDX-FileCopyrightText: 2023 Civic Hacker, LLC
# SPDX-License-Identifier: GPL-3.0-or-later

class SchemaViolation(Exception): pass


class RangeConstraintViolation(SchemaViolation): pass


class LengthConstraintViolation(SchemaViolation): pass


class RequiredPropertyViolation(SchemaViolation): pass


class ValueTypeViolation(SchemaViolation): pass


class SubSchemaFailureViolation(SchemaViolation): pass
