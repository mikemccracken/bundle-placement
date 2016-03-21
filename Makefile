git-sync-requirements:
	if [ ! -f tools/sync-repo.py ]; then echo "Need to download sync-repo.py from https://git.io/v2mEw" && exit 1; fi
	tools/sync-repo.py -m repo-manifest.json -f

pyflakes:
	pyflakes conjure test bin

pep8:
	pep8 conjure test bin

clean:
	@rm -rf cover
	@rm -rf .coverage
	@rm -rf .tox

tox:
	tox
