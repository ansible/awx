export default
    function SetEnabledMsg() {
        return function(host) {
            if (host.has_inventory_sources) {
                // Inventory sync managed, so not clickable
                host.enabledToolTip = (host.enabled) ? 'Host is available' : 'Host is not available';
            }
            else {
                // Clickable
                host.enabledToolTip = (host.enabled) ? 'Host is available. Click to toggle.' : 'Host is not available. Click to toggle.';
            }
        };
    }
