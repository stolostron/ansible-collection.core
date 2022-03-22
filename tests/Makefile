PYTHON_VERSION ?= `python -c 'import platform; print("{0}.{1}".format(platform.python_version_tuple()[0], platform.python_version_tuple()[1]))'`

test-sanity:
	ansible-galaxy collection install amazon.aws
	ansible-test sanity --docker -v --color --python $(PYTHON_VERSION)

test-unit:
	ansible-test units -v --color --docker --coverage --python $(PYTHON_VERSION)
