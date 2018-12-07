checkstyle:
	find . -name '*.py' -exec flake8 --config=.flake8 {} \;
	find . -name '*.py' -exec yapf --diff {} \;
	shellcheck *.sh
    
