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

from functools import lru_cache
import logging
from theblues.charmstore import CharmStore
import yaml

from bundleplacer.charm import Charm
from bundleplacer.assignmenttype import AssignmentType, label_to_atype


log = logging.getLogger('bundleplacer')


class CharmStoreAPI:
    _charmstore = None

    def __init__(self):
        if not CharmStoreAPI._charmstore:
            csurl = 'https://api.jujucharms.com/v4'
            CharmStoreAPI._charmstore = CharmStore(csurl)

    @classmethod
    @lru_cache(maxsize=128)
    def lookup_charm(self, charm_name):
        entity = CharmStoreAPI._charmstore.entity(charm_name)
        return entity


def create_charm_class(servicename, service_dict, servicemeta, relations):
    # some attempts to guess at subordinate status from bundle format,
    # to avoid having to include it in metadata:

    # This doesn't work because bundles with no machines might
    # just use the juju default:

    # is_subordinate = 'to' not in service_dict.keys()

    is_subordinate = service_dict['num_units'] == 0

    charm_name = service_dict['charm'].split('/')[-1]
    charm_name = '-'.join(charm_name.split('-')[:-1])
    entity = CharmStoreAPI().lookup_charm(charm_name)
    display_name = "{} ({})".format(servicename,
                                    entity['Meta']['charm-metadata']['Name'])
    summary = entity['Meta']['charm-metadata']['Summary']

    myrelations = []
    for src, dst in relations:
        if src.startswith(servicename) or dst.startswith(servicename):
            myrelations.append((src, dst))

    charm = Charm(charm_name=servicename,
                  charm_source=service_dict['charm'],
                  display_name=servicemeta.get('display-name', display_name),
                  summary=servicemeta.get('summary', summary),
                  constraints=servicemeta.get('constraints', {}),
                  depends=servicemeta.get('depends', []),
                  conflicts=servicemeta.get('conflicts', []),
                  allowed_assignment_types=servicemeta.get(
                      'allowed_assignment_types',
                      list(AssignmentType)),
                  num_units=service_dict.get('num_units', 1),
                  options=service_dict.get('options', {}),
                  allow_multi_units=servicemeta.get('allow_multi_units', True),
                  subordinate=is_subordinate,
                  required=servicemeta.get('required', True),
                  relations=myrelations)

    # Make sure to map any strings to an assignment type enum
    if any(isinstance(atype, str) for atype in charm.allowed_assignment_types):
        charm.allowed_assignment_types = label_to_atype(
            charm.allowed_assignment_types)
    return charm


class Bundle:
    def __init__(self, filename, metadatafilename):
        self.filename = filename
        self.metadatafilename = metadatafilename
        with open(self.filename) as f:
            self._bundle = yaml.load(f)
        if metadatafilename:
            with open(self.metadatafilename) as f:
                self._metadata = yaml.load(f)
        else:
            self._metadata = {}
        if 'services' not in self._bundle.keys():
            raise Exception("Invalid Bundle.")

    @property
    def charm_classes(self):
        charm_classes = []
        metadata = self._metadata.get('services', {})
        services = self._bundle.get('services', {})
        relations = self._bundle.get('relations', [])
        for servicename, sd in services.items():
            sm = metadata.get(servicename, {})
            charm_classes.append(create_charm_class(servicename, sd,
                                                    sm, relations))
        return charm_classes

    def extra_items(self):
        return {k: v for k, v in self._bundle.items()
                if k not in ['services', 'machines', 'relations']}
