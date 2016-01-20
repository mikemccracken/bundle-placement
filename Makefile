
TOPDIR              := $(shell git rev-parse --show-toplevel)
GIT_REV		    := $(shell git log --oneline -n1| cut -d" " -f1)
VERSION             := $(shell ./tools/version)
UPSTREAM_MAASCLIENT := https://github.com/Ubuntu-Solutions-Engineering/maasclient.git
UPSTREAM_MAASCLIENT_COMMIT := 357db23

.PHONY: install-dependencies
install-dependencies:
	sudo apt-get -yy install devscripts equivs pandoc
	sudo mk-build-deps -i -t "apt-get --no-install-recommends -y" debian/control

.PHONY: uninstall-dependencies
uninstall-dependencies:
	sudo apt-get remove bundle-placer-build-deps

clean:
	@-debian/rules clean
	@rm -rf .coverage
	@rm -rf .tox

DPKGBUILDARGS = -us -uc -i'.git.*|.tox|.bzr.*|.editorconfig|.travis-yaml|maasclient\/debian'
deb-src: clean update_version
	@dpkg-buildpackage -S -sa $(DPKGBUILDARGS)

deb-release:
	@dpkg-buildpackage -S -sd $(DPKGBUILDARGS)

deb: clean update_version man-pages
	@dpkg-buildpackage -b $(DPKGBUILDARGS)

#man-pages:
#	@pandoc -s docs/openstack-juju.rst -t man -o man/en/openstack-juju.1

current_version:
	@echo $(VERSION)

git-sync-requirements:
	@echo Syncing git repos
	rm -rf tmp && mkdir -p tmp
	rm -rf maasclient
	git clone -q $(UPSTREAM_MAASCLIENT) tmp/maasclient
	(cd tmp/maasclient && git checkout -q -f $(UPSTREAM_MAASCLIENT_COMMIT))
	rsync -az --delete tmp/maasclient/maasclient .
	rm -rf tmp

git_rev:
	@echo $(GIT_REV)

update_version: git-sync-requirements
	wrap-and-sort
	@sed -i -r "s/(^__version__\s=\s)(.*)/\1\"$(VERSION)\"/" cloudinstall/__init__.py

.PHONY: ci-test pyflakes pep8 test travis-test
ci-test: pyflakes pep8 travis-test

pyflakes:
	python3 `which pyflakes` bundleplacer bin

pep8:
	pep8 bundleplacer bin

NOSE_ARGS = -v --with-cover --cover-package=bundleplacer --cover-html test --cover-inclusive bundleplacer
test: tox

travis-test:
	nosetests $(NOSE_ARGS)

tox:
	@tox

