export default
    function GetProjectIcon() {
        return function(status) {
            var result = '';
            switch (status) {
                case 'n/a':
                case 'ok':
                case 'never updated':
                    result = 'none';
                    break;
                case 'pending':
                case 'waiting':
                case 'new':
                    result = 'none';
                    break;
                case 'updating':
                case 'running':
                    result = 'running';
                    break;
                case 'successful':
                    result = 'success';
                    break;
                case 'failed':
                case 'missing':
                case 'canceled':
                    result = 'error';
            }
            return result;
        };
    }
