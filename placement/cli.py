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

import argparse
import json
import logging
import os
import sys
import urwid

from cloudinstall.maas import connect_to_maas, MaasMachine

from placement.config import Config
from placement.controller import PlacementController
from placement.log import setup_logger
from placement.placerview import PlacerView
from ubuntui.ev import EventLoop
from ubuntui.palette import STYLES

log = None


class FakeMaasState:

    def machines(self, state=None, constraints=None):
        fakepath = os.getenv("FAKE_API_DATA")
        fn = os.path.join(fakepath, "maas-machines.json")
        with open(fn) as f:
            try:
                nodes = json.load(f)
            except:
                log.exception("Error loading JSON")
                return []
        return [MaasMachine(-1, m) for m in nodes
                if m['hostname'] != 'juju-bootstrap.maas']

    def invalidate_nodes_cache(self):
        "no op"

    def machines_summary(self):
        return "no summary for fake state"


def parse_options(argv):
    parser = argparse.ArgumentParser(description='Juju Bundle Placer',
                                     prog='placer',
                                     argument_default=argparse.SUPPRESS)
    parser.add_argument("bundle_filename", metavar='bundle',
                        help="Bundle file to edit")
    parser.add_argument("--metadata", dest="metadata_filename",
                        metavar='metadatafile',
                        help="Optional metadata file describing constraints "
                        "on services in bundle")
    parser.add_argument("--maas-ip", dest="maas_ip", default=None)
    parser.add_argument("--maas-cred", dest="maas_cred", default=None)
    return parser.parse_args(argv)


def main():
    opts = parse_options(sys.argv[1:])

    config = Config('bundle-placer', opts.__dict__)
    config.save()

    setup_logger(cfg_path=config.cfg_path)
    log = logging.getLogger('placement')

    log.info("Editing file: {}".format(opts.bundle_filename))

    if opts.maas_ip and opts.maas_cred:
        creds = dict(api_host=opts.maas_ip,
                     api_key=opts.maas_cred)
        maas, maas_state = connect_to_maas(creds)
    else:
        maas_state = FakeMaasState()

    placement_controller = PlacementController(config=config,
                                               maas_state=maas_state)

    mainview = PlacerView(placement_controller, config)

    def unhandled_input(key):
        if key in ['q', 'Q']:
            raise urwid.ExitMainLoop()
    EventLoop.build_loop(mainview, STYLES, unhandled_input=unhandled_input)
    mainview.loop = EventLoop.loop
    mainview.update()
    EventLoop.run()
