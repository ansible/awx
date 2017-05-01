export default
    function GetSyncStatusMsg() {
        return function(params) {
            var status = params.status,
            launch_class = '',
            launch_tip = 'Start sync process',
            schedule_tip = 'Schedule future inventory syncs',
            stat, stat_class, status_tip;

            stat = status;
            stat_class = stat;

            switch (status) {
                case 'never updated':
                    stat = 'never';
                stat_class = 'na';
                status_tip = 'Sync not performed. Click <i class="fa fa-refresh"></i> to start it now.';
                break;
                case 'none':
                    case 'ok':
                    case '':
                    launch_class = 'btn-disabled';
                stat = 'n/a';
                stat_class = 'na';
                status_tip = 'Cloud source not configured. Click <i class="fa fa-pencil"></i> to update.';
                launch_tip = 'Cloud source not configured.';
                break;
                case 'canceled':
                    status_tip = 'Sync canceled. Click to view log.';
                break;
                case 'failed':
                    status_tip = 'Sync failed. Click to view log.';
                break;
                case 'successful':
                    status_tip = 'Sync completed. Click to view log.';
                break;
                case 'pending':
                    status_tip = 'Sync pending.';
                launch_class = "btn-disabled";
                launch_tip = "Sync pending";
                break;
                case 'updating':
                    case 'running':
                    launch_class = "btn-disabled";
                launch_tip = "Sync running";
                status_tip = "Sync running. Click to view log.";
                break;
            }

            return {
                "class": stat_class,
                "tooltip": status_tip,
                "status": stat,
                "launch_class": launch_class,
                "launch_tip": launch_tip,
                "schedule_tip": schedule_tip
            };
        };
    }

GetSyncStatusMsg.$inject = [];
