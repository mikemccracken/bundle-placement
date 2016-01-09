

class Charm:
    def __init__(self, charm_name, display_name, constraints,
                 depends, conflicts, allowed_assignment_types,
                 num_units, allow_multi_units, subordinate, required):
        self.charm_name = charm_name
        self.display_name = display_name
        self.constraints = constraints
        self.depends = depends
        self.conflicts = conflicts
        self.allowed_assignment_types = allowed_assignment_types
        self.num_units = num_units
        self.allow_multi_units = allow_multi_units
        self.subordinate = subordinate
        self.is_core = required

    def required_num_units(self):
        return self.num_units

    def __repr__(self):
        return "<Charm {}>".format(self.charm_name)
