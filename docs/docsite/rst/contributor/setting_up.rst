
Setting up your development environment
========================================

The AWX docs are developed using the Python toolchain. The content itself is authored in ReStructuredText (rst).

Prerequisites
---------------

.. contents::
    :local:


Fork and clone the AWX repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have not done so already, you'll need to fork the AWX repo on GitHub. For more on how to do this, see `Fork a Repo <https://help.github.com/articles/fork-a-repo/>`_.


Install python and setuptools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install the setuptools package on Linux using pip:


1. If not already installed, `download the latest version of Python3 <https://www.geeksforgeeks.org/how-to-download-and-install-python-latest-version-on-linux/>`_ on your machine.

2. Check if pip3 and python3 are correctly installed in your system using the following command:

::

	python3 --version
	pip3 --version

3. Upgrade pip3 to the latest version to prevent installation issues:

::

	pip3 install --upgrade pip

4. Install Setuptools:

::

	pip3 install setuptools

5. Verify whether the Setuptools has been properly installed: 

::

	import setuptools

If no errors are returned, then the package was installed properly.

6. Install the tox package so you can build the docs locally:

::

	pip3 install tox



Run local build of the docs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To build the docs on your local machine, use the tox utility. In your forked branch of your AWX repo, run: 

::

	tox -e docs  


Access the AWX user interface
------------------------------

To access an instance of the AWX interface, refer to `Build and run the development environment <https://github.com/ansible/awx/blob/devel/CONTRIBUTING.md#setting-up-your-development-environment>`_ for detail. Once you have your environment setup, you can access the AWX UI by logging into it at `https://localhost:8043 <https://localhost:8043>`_, and access the API directly at `https://localhost:8043/api/ <https://localhost:8043/api/>`_.
