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
from subprocess import Popen, PIPE, TimeoutExpired

from urwid import (AttrMap, Button, Columns, Divider, Filler,
                   GridFlow, Overlay, Padding, Pile, SelectableIcon,
                   Text, WidgetWrap)

from bundleplacer.assignmenttype import AssignmentType

from bundleplacer.ui.machine_chooser import MachineChooser
from bundleplacer.ui.machines_list import MachinesList
from bundleplacer.ui.service_chooser import ServiceChooser
from bundleplacer.ui.services_list import ServicesList
from ubuntui.views import InfoDialogWidget
from ubuntui.widgets import MetaScroll
from bundleplacer.state import CharmState

log = logging.getLogger('bundleplacer')


BUTTON_SIZE = 20


class ServicesColumn(WidgetWrap):

    """Displays dynamic list of unplaced services and associated controls
    """

    def __init__(self, display_controller, placement_controller,
                 placement_view):
        self.display_controller = display_controller
        self.placement_controller = placement_controller
        self.placement_view = placement_view
        w = self.build_widgets()
        super().__init__(w)
        self.update()

    def selectable(self):
        return True

    def build_widgets(self):
        togglefunc = self.display_controller.do_toggle_selected_charm
        self.services_list = ServicesList(self.placement_controller,
                                          togglefunc,
                                          ignore_assigned=False,
                                          ignore_deployed=False,
                                          show_type='all',
                                          title="Services to Place")

        autoplace_func = self.placement_view.do_autoplace
        self.autoplace_button = AttrMap(Button("Auto-place Remaining Services",
                                               on_press=autoplace_func),
                                        'button_secondary',
                                        'button_secondary focus')

        clear_all_func = self.placement_view.do_clear_all
        self.clear_all_button = AttrMap(Button("Clear All Placements",
                                               on_press=clear_all_func),
                                        'button_secondary',
                                        'button_secondary focus')

        self.services_pile = Pile([self.services_list, Divider()])

        self.top_buttons = []
        self.top_button_grid = GridFlow(self.top_buttons,
                                        36, 1, 0, 'center')

        pl = [
            Text(("body", "Services"), align='center'),
            Divider(),
            self.top_button_grid, Divider(),
            self.services_pile, Divider(),
        ]

        self.main_pile = Pile(pl)

        return self.main_pile

    def update(self):
        self.services_list.update()

        top_buttons = []
        unplaced = self.placement_controller.unassigned_undeployed_services()
        if len(unplaced) == 0:
            icon = SelectableIcon(" (Auto-place Remaining Services) ")
            top_buttons.append((AttrMap(icon,
                                        'disabled_button',
                                        'disabled_button_focus'),
                                self.top_button_grid.options()))

        else:
            top_buttons.append((self.autoplace_button,
                                self.top_button_grid.options()))

        top_buttons.append((self.clear_all_button,
                            self.top_button_grid.options()))

        self.deploy_button = AttrMap(
            Button("Deploy",
                   on_press=self.placement_view.do_deploy),
            'button_primary', 'button_primary focus')

        top_buttons.append((self.deploy_button,
                            self.top_button_grid.options()))
        self.top_button_grid.contents = top_buttons

    def do_reset_to_defaults(self, sender):
        self.placement_controller.set_all_assignments(
            self.placement_controller.gen_defaults())

    def do_place_subordinate(self, sender, charm_class):
        sub_placeholder = self.placement_controller.sub_placeholder
        self.placement_controller.assign(sub_placeholder,
                                         charm_class,
                                         AssignmentType.BareMetal)


class MachinesColumn(WidgetWrap):

    """Shows machines or a link to MAAS to add more"""

    def __init__(self, display_controller, placement_controller,
                 placement_view):
        self.display_controller = display_controller
        self.placement_controller = placement_controller
        self.placement_view = placement_view
        w = self.build_widgets()
        super().__init__(w)
        self.update()

    def selectable(self):
        return True

    def build_widgets(self):

        def has_services_p(m):
            pc = self.placement_controller
            n = sum([len(al) for at, al in
                     pc.assignments_for_machine(m).items()])
            return n > 0

        self.open_maas_button = AttrMap(Button("Open in Browser",
                                               on_press=self.browse_maas),
                                        'button_secondary',
                                        'button_secondary focus')

        bc = self.placement_view.config.juju_env['bootstrap-config']
        maasname = "'{}' <{}>".format(bc['name'], bc['maas-server'])
        maastitle = "Connected to MAAS {}".format(maasname)
        tw = Columns([Text(maastitle),
                      Padding(self.open_maas_button, align='right',
                              width=BUTTON_SIZE, right=2)])

        togglefunc = self.display_controller.do_toggle_selected_machine
        self.machines_list = MachinesList(self.placement_controller,
                                          togglefunc,
                                          show_hardware=True,
                                          show_assignments=False,
                                          show_placeholders=False,
                                          title_widgets=tw)
        self.machines_list.update()

        self.machines_list_pile = Pile([self.machines_list,
                                        Divider()])

        # placeholders replaced in update() with absolute indexes, so
        # if you change this list, check update().
        pl = [Text(('body', "Machines {}".format(MetaScroll().get_text()[0])),
                   align='center'),
              Divider(),
              Pile([]),         # machines_list
              Divider()]

        self.main_pile = Pile(pl)

        return self.main_pile

    def update(self):
        self.machines_list.update()

        bc = self.placement_view.config.juju_env['bootstrap-config']
        empty_maas_msg = ("There are no available machines.\n"
                          "Open {} to add machines to "
                          "'{}':".format(bc['maas-server'], bc['name']))

        self.empty_maas_widgets = Pile([Text([('error_icon',
                                               "\N{WARNING SIGN} "),
                                              empty_maas_msg],
                                             align='center'),
                                        Padding(self.open_maas_button,
                                                align='center',
                                                width=BUTTON_SIZE)])

        # 2 machines is the subordinate placeholder + juju default:
        if len(self.placement_controller.machines()) == 2:
            self.main_pile.contents[2] = (self.empty_maas_widgets,
                                          self.main_pile.options())
        else:
            self.main_pile.contents[2] = (self.machines_list_pile,
                                          self.main_pile.options())

    def browse_maas(self, sender):

        bc = self.placement_view.config.juju_env['bootstrap-config']
        try:
            p = Popen(["sensible-browser", bc['maas-server']],
                      stdout=PIPE, stderr=PIPE)
            outs, errs = p.communicate(timeout=5)

        except TimeoutExpired:
            # went five seconds without an error, so we assume it's
            # OK. Don't kill it, just let it go:
            return
        e = errs.decode('utf-8')
        msg = "Error opening '{}' in a browser:\n{}".format(bc['name'], e)

        w = InfoDialogWidget(msg, self.placement_view.remove_overlay)
        self.placement_view.show_overlay(w)


class ActionsColumn(WidgetWrap):

    """Displays dynamic list of unplaced services and associated controls
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
        self.update()

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

        self.actions_column = ActionsColumn(self.display_controller,
                                            self.placement_controller,
                                            self)
        
        self.columns = Columns([self.services_column,
                                self.machines_column,
                                self.actions_column])
        self.main_pile = Pile([Padding(self.columns,
                                       align='center',
                                       width=('relative', 95))])
        return Filler(self.main_pile, valign='top')

    def update(self):
        self.services_column.update()
        self.machines_column.update()
        self.actions_column.update()

    def do_autoplace(self, sender):
        ok, msg = self.placement_controller.autoassign_unassigned_services()
        if not ok:
            self.show_overlay(InfoDialogWidget(msg, self.remove_overlay))

    def do_clear_all(self, sender):
        self.placement_controller.clear_all_assignments()

    def do_clear_machine(self, sender, machine):
        self.placement_controller.clear_assignments(machine)

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
