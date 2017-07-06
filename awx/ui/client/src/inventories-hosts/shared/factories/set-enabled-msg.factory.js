export default
    function SetEnabledMsg(i18n) {
        return function(host) {
            if (host.has_inventory_sources) {
                // Inventory sync managed, so not clickable
                host.enabledToolTip = (host.enabled) ? i18n._('Host is available') : i18n._('Host is not available');
            }
            else {
                // Clickable
                host.enabledToolTip = (host.enabled) ? i18n._('Host is available. Click to toggle.') : i18n._('Host is not available. Click to toggle.');
            }
        };
    }

SetEnabledMsg.$inject =
    [   'i18n',   ];
