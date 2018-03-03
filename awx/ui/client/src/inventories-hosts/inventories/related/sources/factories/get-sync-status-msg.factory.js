export default
    function GetSyncStatusMsg(i18n) {
        return function(params) {
            var status = params.status,
            launch_class = '',
            launch_tip = i18n._('Start sync process'),
            schedule_tip = i18n._('Schedule inventory syncs'),
            stat, stat_class, status_tip;

            stat = status;
            stat_class = stat;

            switch (status) {
                case 'never updated':
                    stat = 'never';
                stat_class = 'na';
                status_tip = i18n._('Sync not performed. Click') + ' <i class="fa fa-refresh"></i> ' + i18n._('to start it now.');
                break;
                case 'none':
                    case 'ok':
                    case '':
                    launch_class = 'btn-disabled';
                stat = 'n/a';
                stat_class = 'na';
                status_tip = i18n._('Cloud source not configured. Click') + ' <i class="fa fa-pencil"></i> ' + i18n._('to update.');
                launch_tip = i18n._('Cloud source not configured.');
                break;
                case 'canceled':
                    status_tip = i18n._('Sync canceled. Click to view log.');
                break;
                case 'failed':
                    status_tip = i18n._('Sync failed. Click to view log.');
                break;
                case 'successful':
                    status_tip = i18n._('Sync completed. Click to view log.');
                break;
                case 'pending':
                    status_tip = i18n._('Sync pending.');
                launch_class = "btn-disabled";
                launch_tip = "Sync pending";
                break;
                case 'updating':
                    case 'running':
                    launch_class = "btn-disabled";
                launch_tip = i18n._("Sync running");
                status_tip = i18n._("Sync running. Click to view log.");
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

GetSyncStatusMsg.$inject = ['i18n'];
