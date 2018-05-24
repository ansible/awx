
import awx.network_ui.routing


def test_routing():
    '''
    Tests that the number of routes in awx.network_ui.routing is 3.
    '''
    assert len(awx.network_ui.routing.channel_routing) == 3
