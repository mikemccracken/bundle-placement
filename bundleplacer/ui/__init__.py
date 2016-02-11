# Copyright 2014-2016 Canonical, Ltd.
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

from urwid import (AttrMap, Button, Columns, Divider, Filler, Overlay,
                   Padding, Pile, Text, WidgetWrap)

from bundleplacer.assignmenttype import AssignmentType

from bundleplacer.ui.services_column import ServicesColumn
from bundleplacer.ui.machines_column import MachinesColumn
from bundleplacer.ui.machine_chooser import MachineChooser
from bundleplacer.ui.service_chooser import ServiceChooser


log = logging.getLogger('bundleplacer')


BUTTON_SIZE = 20


class ActionsColumn(WidgetWrap):

    """Displays dynamic list of buttons to place selected services on
    selected machines.

    """

    def __init__(self, display_controller, placement_controller,
                 placement_view):
        self.display_controller = display_controller
        self.placement_controller = placement_controller
        self.placement_view = placement_view
        self.showing_buttons = False
        w = self.build_widgets()
        super().__init__(w)
        self.update()

    def selectable(self):
        return True

    def build_widgets(self):
        self.info_label = Text("", align='center')
        pl = [
            Text(("body", "Container Type"), align='center'),
            Divider(),
            self.info_label,
            Divider()
        ]
        self.action_buttons = []
        self.update_buttons()

        self.main_pile = Pile(pl)

        return self.main_pile

    def update(self):
        selected_charms = self.display_controller.selected_charms

        if len(selected_charms) == 0:
            self.showing_buttons = False
            charmstr = "No Charms Selected"
        else:
            charmstr = "Charms: " + ", ".join([m.charm_name
                                               for m in selected_charms])

        selected_machines = self.display_controller.selected_machines

        if len(selected_machines) == 0:
            self.showing_buttons = False
            machinestr = "No Machines Selected"
        else:
            machinestr = "Machines: " + ", ".join([m.hostname for m
                                                   in selected_machines])

        self.info_label.set_text(("info",
                                  "Select container type to place:\n"
                                  "{}\n{}".format(charmstr, machinestr)))

        if len(selected_charms) == 0 or len(selected_machines) == 0:
            self.main_pile.contents[-1] = (Divider(),
                                           self.main_pile.options())
            self.showing_buttons = False
            return

        button_count_changed = self.update_buttons()
        # only change the pile if we were previously not showing it:
        if not self.showing_buttons or button_count_changed:
            self.main_pile.contents[-1] = (Pile(self.action_buttons),
                                           self.main_pile.options())
            self.showing_buttons = True

    def update_buttons(self):
        all_actions = [(AssignmentType.BareMetal,
                        'Add as Bare Metal',
                        self.display_controller.do_select_baremetal),
                       (AssignmentType.LXC,
                        'Add as LXC',
                        self.display_controller.do_select_lxc),
                       (AssignmentType.KVM,
                        'Add as KVM',
                        self.display_controller.do_select_kvm)]

        selected_charms = self.display_controller.selected_charms

        allowed_sets = [set(sc.allowed_assignment_types)
                        for sc in selected_charms]
        allowed_types = set([atype for atype, _, _ in all_actions])
        allowed_types = allowed_types.intersection(*allowed_sets)

        prev_len = len(self.action_buttons)
        self.action_buttons = [AttrMap(Button(label, on_press=func),
                                       'button_secondary',
                                       'button_secondary focus')
                               for atype, label, func in all_actions
                               if atype in allowed_types]

        return len(self.action_buttons) != prev_len

    def focus_top(self):
        self.update()
        try:
            newpos = len(self.main_pile.contents) - 1
            self.main_pile.focus_position = newpos
        except IndexError:
            log.debug("caught indexerror?")
            pass


class PlacementView(WidgetWrap):

    """
    Handles display of machines and services.

    displays nothing if self.controller is not set.
    set it to a PlacementController.

    :param do_deploy_cb: deploy callback from controller
    """

    def __init__(self, display_controller, placement_controller,
                 config, do_deploy_cb):
        self.display_controller = display_controller
        self.placement_controller = placement_controller
        self.config = config
        self.do_deploy_cb = do_deploy_cb

        w = self.build_widgets()
        super().__init__(w)
        self.reset_selections(top=True)  # calls self.update

    def scroll_down(self):
        pass

    def scroll_up(self):
        pass

    def build_widgets(self):
        self.services_column = ServicesColumn(self.display_controller,
                                              self.placement_controller,
                                              self)

        self.machines_column = MachinesColumn(self.display_controller,
                                              self.placement_controller,
                                              self)

        self.columns = Columns([self.services_column,
                                self.machines_column])

        self.deploy_button = Button("Deploy", on_press=self.do_deploy)

        self.main_pile = Pile([Padding(self.columns,
                                       align='center',
                                       width=('relative', 95)),
                               AttrMap(self.deploy_button,
                                       'button_primary',
                                       'button_primary focus')])
        return Filler(self.main_pile, valign='top')

    def update(self):
        self.services_column.update()
        self.machines_column.update()

        unplaced = self.placement_controller.unassigned_undeployed_services()
        all = self.placement_controller.charm_classes()
        n_total = len(all)
        remaining = len(unplaced) + len([c for c in all if c.subordinate])
        dmsg = "Deploy (Auto-assigning {}/{} charms)".format(remaining,
                                                             n_total)
        self.deploy_button.set_label(dmsg)

    def do_clear_all(self, sender):
        self.placement_controller.clear_all_assignments()

    def do_clear_machine(self, sender, machine):
        self.placement_controller.clear_assignments(machine)

    def reset_selections(self, top=False):
        self.services_column.clear_selections()
        self.machines_column.clear_selections()
        self.update()
        self.columns.focus_position = 0

        if top:
            self.services_column.focus_top()
        else:
            self.services_column.focus_next()

    def focus_machines_column(self):
        self.columns.focus_position = 1
        self.machines_column.focus_prev_or_top()

    def do_show_service_chooser(self, sender, machine):
        self.show_overlay(ServiceChooser(self.placement_controller,
                                         machine,
                                         self))

    def do_deploy(self, sender):
        self.do_deploy_cb()

    def do_show_machine_chooser(self, sender, charm_class):
        self.show_overlay(MachineChooser(self.placement_controller,
                                         charm_class,
                                         self))

    def show_overlay(self, overlay_widget):
        self.orig_w = self._w
        self._w = Overlay(top_w=overlay_widget,
                          bottom_w=self._w,
                          align='center',
                          width=('relative', 60),
                          min_width=80,
                          valign='middle',
                          height='pack')

    def remove_overlay(self, overlay_widget):
        # urwid note: we could also get orig_w as
        # self._w.contents[0][0], but this is clearer:
        self._w = self.orig_w
