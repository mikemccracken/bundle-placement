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


from urwid import AttrMap, Button, Padding, WidgetWrap, SelectableIcon

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

        pad_adj = 0
        if self.charm_class.subordinate:
            self.button = SelectableIcon("I AM A SUBORDINATE SERVICE")
            pad_adj = 2
        else:
            self.button = Button("I AM A SERVICE", self.do_action)

        if self.is_selected:
            return Padding(AttrMap(self.button, 'deploy_highlight_start',
                                   'button_secondary focus'),
                           left=2+pad_adj,
                           right=2+pad_adj)
        else:
            return Padding(AttrMap(self.button, 'text',
                                   'button_secondary focus'),
                           left=2+pad_adj,
                           right=2+pad_adj)

    def update(self):
        self._w = self.build_widgets()

        if self.is_selected:
            accent_style = "deploy_highlight_start"  # was "label"
            selection_markup = [(accent_style, "\n\N{BALLOT BOX WITH CHECK} ")]
        else:
            accent_style = "text"
            selection_markup = [(accent_style, "\n\N{BALLOT BOX} ")]

        if self.charm_class.subordinate:
            self.button.set_text([("\n")] + self.title_markup)
            return

        markup = selection_markup + self.title_markup

        state, cons, deps = self.controller.get_charm_state(self.charm_class)

        if state == CharmState.REQUIRED:
            p = self.controller.get_assignments(self.charm_class)
            nr = self.charm_class.required_num_units()
            info_str = " ({} of {} placed)".format(len(p), nr)

            # Add hint to explain why a dep showed up in required
            if len(p) == 0 and len(deps) > 0:
                dep_str = ", ".join([c.display_name for c in deps])
                info_str += " - required by {}".format(dep_str)

            markup.append((accent_style, info_str))
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
        # markup += ["    ", ('label', "Assignments: ")]
        # ad = self.controller.get_assignments(self.charm_class)
        # markup += string_for_placement_dict(ad)

        self.button.set_label(markup)

    def do_action(self, sender):
        self.is_selected = not self.is_selected
        self.action(self)
