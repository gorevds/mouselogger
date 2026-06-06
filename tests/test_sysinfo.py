from mouselogger import sysinfo


def test_os_name_non_empty():
    assert isinstance(sysinfo.os_name(), str)
    assert sysinfo.os_name()


def test_screen_size_is_pair():
    size = sysinfo.screen_size()
    assert isinstance(size, tuple) and len(size) == 2


def test_make_dpi_aware_is_safe():
    # на не-Windows это no-op и не должно бросать
    sysinfo.make_dpi_aware()
