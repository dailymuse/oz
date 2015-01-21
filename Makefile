lint:
	pylint -d line-too-long -d bad-whitespace -d invalid-name -d wildcard-import -d broad-except -d global-statement oz

release:
	git checkout master
	git merge develop
	git push origin master
	python setup.py clean build sdist upload
