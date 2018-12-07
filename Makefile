checkstyle:
	find . -name '*.py' -exec flake8 --config=.flake8 {} \;
	shellcheck *.sh
