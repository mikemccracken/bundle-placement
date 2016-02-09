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

import logging

from urwid import AttrMap, WidgetWrap, SelectableIcon

from bundleplacer.maas import MaasMachineStatus
from ubuntui.widgets.buttons import MenuSelectButton

log = logging.getLogger('bundleplacer')


class SimpleMachineWidget(WidgetWrap):

    """A widget displaying a machine. Simplified.

    machine - the machine to display

    action - action function to call. passed this widget.

    controller - a PlacementController instance

    show_assignments - display info about which charms are assigned
    and what assignment type (LXC, KVM, etc) they have.
    """

    def __init__(self, machine, action, controller, show_assignments=True):
        self.machine = machine
        self.action = action
        self.controller = controller
        self.show_assignments = show_assignments
        self.is_selected = False
        w = self.build_widgets()
        self.update()
        super().__init__(w)

    def selectable(self):
        return True

    def hardware_info_markup(self):
        m = self.machine
        return ['arch: {}  '.format(m.arch),
                'cores: {}  '.format(m.cpu_cores),
                'mem: {}  '.format(m.mem),
                'storage: {}'.format(m.storage)]

    def build_widgets(self):

        if not self.machine_is_selectable():
            self.button = SelectableIcon("I am an unavailable machine")
        else:
            self.button = MenuSelectButton("I AM A MACHINE", self.do_action)

        if self.is_selected:
            return AttrMap(self.button, 'deploy_highlight_start',
                           'button_secondary focus')
        else:
            return AttrMap(self.button, 'text',
                           'button_secondary focus')
            
    def update_machine(self):
        """Refresh with potentially updated machine info from controller.
        Assumes that machine exists - machines going away is handled
        in machineslist.update().
        """
        self.machine = next((m for m in self.controller.machines()
                             if m.instance_id == self.machine.instance_id),
                            None)

    def machine_is_selectable(self):
        return self.machine.status == MaasMachineStatus.READY

    def update(self):
        self.update_machine()
        self._w = self.build_widgets()

        if not self.machine_is_selectable():
            markup = ["\N{TAPE DRIVE} {}".format(self.machine.hostname),
                      " ({})\n".format(self.machine.status)]
            self.button.set_text([("\n  ")] + markup)
            return

        if self.is_selected:
            markup = ["\n\N{BALLOT BOX WITH CHECK} "]
        else:
            markup = ["\n\N{BALLOT BOX} "]
            
        if self.machine == self.controller.sub_placeholder:
            markup += [('error', "SHOULD NOT SHOW PLACEHOLDER FOR SUBS")]
        elif self.machine == self.controller.def_placeholder:
            markup += [('error', "DEFAULT PLACEHOLDER SHOULD NOT SHOW!")]
        else:
            markup += ["\N{TAPE DRIVE} {}".format(self.machine.hostname),
                       (" ({})\n".format(self.machine.status))]
            markup += self.hardware_info_markup()

            
        # ad = self.controller.assignments_for_machine(self.machine)
        # astr = [('label', "  Services: ")]

        # for atype, al in ad.items():
        #     n = len(al)
        #     if n == 1:
        #         pl_s = ""
        #     else:
        #         pl_s = "s"
        #     if atype == AssignmentType.BareMetal:
        #         astr.append(('label', "\n    {} service{}"
        #                      " on Bare Metal: ".format(n, pl_s)))
        #     else:
        #         astr.append(('label', "\n    {} "
        #                      "{}{}: ".format(n, atype.name, pl_s)))
        #     if n == 0:
        #         astr.append("\N{EMPTY SET}")
        #     else:
        #         astr.append(", ".join(["\N{GEAR} {}".format(c.display_name)
        #                                for c in al]))

        # if self.machine == self.controller.sub_placeholder:
        #     assignments_text = ''
        #     for _, al in ad.items():
        #         charm_txts = ["\N{GEAR} {}".format(c.display_name)
        #                       for c in al]
        #         assignments_text += ", ".join(charm_txts)
        # else:
        #     assignments_text = astr

        # self.assignments_widget.set_text(assignments_text)

        self.button.set_label(markup)

    def do_action(self, sender):
        self.is_selected = not self.is_selected
        self.update()
        self.action(self)
