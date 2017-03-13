export default
    function GetProjectToolTip(i18n) {
        return function(status) {
            var result = '';
            switch (status) {
                case 'n/a':
                case 'ok':
                case 'never updated':
                    result = i18n._('No SCM updates have run for this project');
                    break;
                case 'pending':
                case 'waiting':
                case 'new':
                    result = i18n._('Queued. Click for details');
                    break;
                case 'updating':
                case 'running':
                    result = i18n._('Running! Click for details');
                    break;
                case 'successful':
                    result = i18n._('Success! Click for details');
                    break;
                case 'failed':
                    result = i18n._('Failed. Click for details');
                    break;
                case 'missing':
                    result = i18n._('Missing. Click for details');
                    break;
                case 'canceled':
                    result = i18n._('Canceled. Click for details');
                    break;
            }
            return result;
        };
    }

GetProjectToolTip.$inject =
    [   'i18n'   ];
