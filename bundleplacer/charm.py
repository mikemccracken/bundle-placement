# Copyright 2015-2016 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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
        self.isolate = True

    def required_num_units(self):
        return self.num_units

    def __repr__(self):
        return "<Charm {}>".format(self.__dict__)
