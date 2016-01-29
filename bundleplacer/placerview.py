# -*- mode: python; -*-
#
# Copyright 2015 Canonical, Ltd.
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

from urwid import WidgetWrap
from bundleplacer.ui import PlacementView
from ubuntui.ev import EventLoop
from ubuntui.frame import Frame

log = logging.getLogger('bundleplacer')


class PlacerUI(Frame):
    def __init__(self, placerview):
        super().__init__(body=placerview)


class PlacerView(WidgetWrap):
    def __init__(self, placement_controller, config, cb):
        self.placement_controller = placement_controller
        self.config = config
        self.cb = cb
        self._selected_machines = set()
        self._selected_charms = set()
        self.pv = PlacementView(
            display_controller=self,
            placement_controller=self.placement_controller,
            config=self.config,
            do_deploy_cb=self.done_cb)
        super().__init__(self.pv)

    def update(self, *args, **kwargs):
        self.pv.update()
        EventLoop.set_alarm_in(1, self.update)

    def status_error_message(self, message):
        pass

    def status_info_message(self, message):
        pass

    def done_cb(self):
        self.cb()

    def do_toggle_selected_machine(self, machinewidget):
        m = machinewidget.machine
        if m in self._selected_machines:
            self._selected_machines.remove(m)
        else:
            self._selected_machines.add(m)

    @property
    def selected_machines(self):
        return list(self._selected_machines)

    def do_toggle_selected_charm(self, servicewidget):
        charm_class = servicewidget.charm_class
        if charm_class in self._selected_charms:
            self._selected_charms.remove(charm_class)
        else:
            self._selected_charms.add(charm_class)

    @property
    def selected_charms(self):
        return list(self._selected_charms)

        
