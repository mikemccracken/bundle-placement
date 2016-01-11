# bundle-placer

Bundle Machine Placement UI for Juju

## testing
This is part of a larger project, but it can also be run standalone.

To give this a try without building a package and installing, use the setup.py script:

```
python setup.py develop --install-dir=`pwd`
```

using `pwd` puts the binary in the current dir, but making that anywhere on your `$PYTHONPATH` is fine.

then to give it a try with a sample bundle and faked MAAS machines:

```
python3 ./bundle-placer share/data-analytics-with-sql-like.yaml --metadata share/data-analytics-with-sql-like-metadata.yaml
```


# copyright
Copyright (C) 2016  Canonical, Ltd.

# license
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

