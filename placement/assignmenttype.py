
from enum import Enum


class AssignmentType(Enum):
    # both are equivalent to not specifying a type to juju:
    DEFAULT = 1
    BareMetal = 1
    KVM = 2
    LXC = 3
