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

from urwid import (AttrMap, Button, Columns, Divider, Padding,
                   Pile, Text, WidgetWrap)

from bundleplacer.ui.machines_list import MachinesList
from ubuntui.views import InfoDialogWidget
from ubuntui.widgets import MetaScroll


log = logging.getLogger('bundleplacer')


BUTTON_SIZE = 20


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
                                          show_only_ready=True,
                                          title_widgets=tw)
        self.machines_list.update()

        self.machines_list_pile = Pile([self.machines_list,
                                        Divider()])

        # placeholders replaced in update() with absolute indexes, so
        # if you change this list, check update().
        pl = [Text(('body',
                    "Ready Machines {}".format(MetaScroll().get_text()[0])),
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

    def clear_selections(self):
        for mw in self.machines_list.machine_widgets:
            mw.is_selected = False

    def focus_prev_or_top(self):
        self.update()
        try:
            self.main_pile.focus_position = 2
            self.machines_list_pile.focus_position = 0
            self.machines_list.focus_prev_or_top()
        except IndexError:
            log.debug("caught indexerror in machinesColumn focus_prev_or_top")
            pass
