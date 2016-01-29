# Copyright 2016 Canonical, Ltd.
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


from urwid import (AttrMap, Button, GridFlow,
                   Padding, Pile, SelectableIcon, Text, WidgetWrap)

from bundleplacer.utils import format_constraint
from bundleplacer.state import CharmState


class SimpleServiceWidget(WidgetWrap):

    """A widget displaying a service as a button

    charm_class - the class describing the service to display

    controller - a PlacementController instance

    action - a function to be called when the button is pressed. The
    service will be passed to the function as userdata.

    show_placements - display the machine(s) currently assigned to
    host this service, both planned deployments (aka 'assignments',
    and already-deployed, called 'deployments').

    """

    def __init__(self, charm_class, controller, action,
                 show_placements=False):
        self.charm_class = charm_class
        self.controller = controller
        self.action = action
        self.show_placements = show_placements
        self.is_selected = False
        w = self.build_widgets()
        self.update()
        super().__init__(w)

    def selectable(self):
        return True

    def update_title_markup(self):
        dn = self.charm_class.display_name
        self.title_markup = ["\N{GEAR} {}".format(dn), ""]
        summary = self.charm_class.summary
        if summary != "":
            self.title_markup.append("\n {}\n".format(summary))

    def build_widgets(self):
        self.update_title_markup()

        self.button = Button("I AM A SERVICE", self.do_action)

        return Padding(self.button, left=2, right=2)

    def update(self):
        self.update_title_markup()
        markup = self.title_markup

        state, cons, deps = self.controller.get_charm_state(self.charm_class)

        if state == CharmState.REQUIRED:
            p = self.controller.get_assignments(self.charm_class)
            d = self.controller.get_deployments(self.charm_class)
            nr = self.charm_class.required_num_units()
            info_str = " ({} of {} placed".format(len(p), nr)
            if len(d) > 0:
                info_str += ", {} deployed)".format(len(d))
            else:
                info_str += ")"

            # Add hint to explain why a dep showed up in required
            if len(p) == 0 and len(deps) > 0:
                dep_str = ", ".join([c.display_name for c in deps])
                info_str += " - required by {}".format(dep_str)

            markup.append(('info', info_str))
        elif state == CharmState.CONFLICTED:
            raise Exception("CONFLICTED not supported by simple widget")
        elif state == CharmState.OPTIONAL:
            pass

        def string_for_placement_dict(d):
            s = []
            for atype, ml in d.items():
                n = len(ml)
                s.append(('label', "    {} ({}): ".format(atype.name, n)))
                if len(ml) == 0:
                    s.append("\N{DOTTED CIRCLE}")
                else:
                    s.append(", ".join(["\N{TAPE DRIVE} {}".format(m.hostname)
                                        for m in ml]))
            if len(s) == 0:
                return [('label', "None")]
            return s
        markup += ["    ", ('label', "Assignments: ")]
        ad = self.controller.get_assignments(self.charm_class)
        dd = self.controller.get_deployments(self.charm_class)
        markup += string_for_placement_dict(ad)
        # mstr += ["\n    ", ('label', "Deployments: ")]
        # mstr += string_for_placement_dict(dd)

        self.button.set_label(markup)

    def do_action(self, sender):
        self.is_selected = not self.is_selected
        self.action(self)
