fixtures
========

This is a module for defining stand-alone fixtures. Ideally a fixture will implement a single item.
DO NOT decorate fixtures in this module with the @pytest.fixture. These fixtures are to be combined
with fixture factories and composition using the `conftest.py` convention. Those composed fixtures
will be decorated for usage and discovery.
