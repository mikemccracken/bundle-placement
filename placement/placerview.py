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


from urwid import Frame, WidgetWrap

from placement.ui import PlacementView

class PlacerView(WidgetWrap):

    def __init__(self, placement_controller, loop, config):
        pv = PlacementView(display_controller=self,
                           placement_controller=placement_controller,
                           loop=loop,
                           config=config, do_deploy_cb=self.done_cb)
        super().__init__(pv)

    def status_error_message(self, message):
        pass

    def status_info_message(self, message):
        pass
        
    def done_cb(self):
        pass
