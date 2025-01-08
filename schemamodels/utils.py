from re import sub


def generate_classname(title: str) -> str:
    return sub(r'(-|_)+', '', title.title())


def is_schema_object(schema: dict) -> bool:
    reqkws = {'type', 'properties'}
    if not reqkws <= schema.keys() or schema.get('type', None) != 'object':
        return False
    return True


def is_schema_toplevel_object(schema: dict) -> bool:
    reqkws = {'title', 'type', 'properties'}
    if not reqkws <= schema.keys() or schema.get('type', None) != 'object':
        return False
    return True
