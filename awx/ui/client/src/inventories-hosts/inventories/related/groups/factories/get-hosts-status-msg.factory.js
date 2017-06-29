export default
    ['i18n', function(i18n) {
        return function(params) {
            var active_failures = params.active_failures,
            total_hosts = params.total_hosts,
            tip, failures, html_class;

            // Return values for use on host status indicator

            if (active_failures > 0) {
                tip = total_hosts + ((total_hosts === 1) ? ' host' : ' hosts') + '. ' + active_failures + i18n._(' with failed jobs.');
                html_class = 'error';
                failures = true;
            } else {
                failures = false;
                if (total_hosts === 0) {
                    // no hosts
                    tip = i18n._("Contains 0 hosts.");
                    html_class = 'none';
                } else {
                    // many hosts with 0 failures
                    tip = total_hosts + ((total_hosts === 1) ? ' host' : ' hosts') + '. ' + i18n._('No job failures');
                    html_class = 'success';
                }
            }

            return {
                tooltip: tip,
                failures: failures,
                'class': html_class
            };
        };
    }];
