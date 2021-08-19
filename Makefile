checkstyle:
	find . -name '*.py' -exec flake8 --config=setup.cfg {} \;
	find . -name '*.py' -exec yapf --diff {} \;
	shellcheck *.sh
    
