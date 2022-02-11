import pytest

from unittest import mock

from awx.main.utils.common import (
    convert_mem_str_to_bytes,
    get_mem_effective_capacity,
    get_corrected_memory,
    convert_cpu_str_to_decimal_cpu,
    get_cpu_effective_capacity,
    get_corrected_cpu,
)


@pytest.mark.parametrize(
    "value,converted_value,mem_capacity",
    [
        ('2G', 2000000000, 19),
        ('4G', 4000000000, 38),
        ('2Gi', 2147483648, 20),
        ('2.1G', 1, 1),  # expressing memory with non-integers is not supported, and we'll fall back to 1 fork for memory capacity.
        ('4Gi', 4294967296, 40),
        ('2M', 2000000, 1),
        ('3M', 3000000, 1),
        ('2Mi', 2097152, 1),
        ('2048Mi', 2147483648, 20),
        ('4096Mi', 4294967296, 40),
        ('64G', 64000000000, 610),
        ('64Garbage', 1, 1),
    ],
)
def test_SYSTEM_TASK_ABS_MEM_conversion(value, converted_value, mem_capacity):
    with mock.patch('django.conf.settings') as mock_settings:
        mock_settings.SYSTEM_TASK_ABS_MEM = value
        mock_settings.SYSTEM_TASK_FORKS_MEM = 100
        mock_settings.IS_K8S = True
        assert convert_mem_str_to_bytes(value) == converted_value
        assert get_corrected_memory(-1) == converted_value
        assert get_mem_effective_capacity(-1) == mem_capacity


@pytest.mark.parametrize(
    "value,converted_value,cpu_capacity",
    [
        ('2', 2.0, 8),
        ('1.5', 1.5, 6),
        ('100m', 0.1, 1),
        ('2000m', 2.0, 8),
        ('4MillionCPUm', 1.0, 4),  # Any suffix other than 'm' is not supported, we fall back to 1 CPU
        ('Random', 1.0, 4),  # Any setting value other than integers, floats millicores (e.g 1, 1.0, or 1000m) is not supported, fall back to 1 CPU
        ('2505m', 2.5, 10),
        ('1.55', 1.6, 6),
    ],
)
def test_SYSTEM_TASK_ABS_CPU_conversion(value, converted_value, cpu_capacity):
    with mock.patch('django.conf.settings') as mock_settings:
        mock_settings.SYSTEM_TASK_ABS_CPU = value
        mock_settings.SYSTEM_TASK_FORKS_CPU = 4
        assert convert_cpu_str_to_decimal_cpu(value) == converted_value
        assert get_corrected_cpu(-1) == converted_value
        assert get_cpu_effective_capacity(-1) == cpu_capacity
