checkstyle:
	find . -name '*.py' -exec flake8 {} \;
	find . -name '*.py' -exec yapf --diff {} \;
	shellcheck *.sh
    
