from dataclasses import FrozenInstanceError

class SchemaViolation(Exception): pass

class RangeConstraintViolation(SchemaViolation): pass
class RequiredPropertyViolation(SchemaViolation): pass

class ValueTypeViolation(SchemaViolation): pass
