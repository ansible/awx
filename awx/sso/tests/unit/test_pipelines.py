import pytest


@pytest.mark.parametrize(
    "lib",
    [
        ("social_pipeline"),
    ],
)
def test_module_loads(lib):
    module = __import__("awx.sso." + lib)  # noqa
