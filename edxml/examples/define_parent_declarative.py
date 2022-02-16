from edxml.ontology import EventTypeFactory


class FileSystemTypes(EventTypeFactory):
    TYPES = ['dir', 'file']
    TYPE_PROPERTIES = {
        'dir': {'name': 'filesystem-name'},
        'file': {'dir': 'filesystem-name'}
    }
    TYPE_HASHED_PROPERTIES = {
        'dir': ['name'],
        'file': ['dir']
    }
    PARENT_MAPPINGS = {
        'file': {'dir': 'name'}
    }
    PARENTS_CHILDREN = [
        ['dir', 'containing', 'file']
    ]

    CHILDREN_SIBLINGS = [
        ['file', 'contained in', 'dir']
    ]
