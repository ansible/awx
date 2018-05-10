export default function GetTargetTitle(i18n) {
    return function (target) {

        var rtnTitle = i18n._('ALL ACTIVITY');

        switch(target) {
            case 'project':
                rtnTitle = i18n._('PROJECTS');
                break;
            case 'credential_type':
                rtnTitle = i18n._('CREDENTIAL TYPES');
                break;
            case 'inventory':
                rtnTitle = i18n._('INVENTORIES');
                break;
            case 'credential':
                rtnTitle = i18n._('CREDENTIALS');
                break;
            case 'user':
                rtnTitle = i18n._('USERS');
                break;
            case 'team':
                rtnTitle = i18n._('TEAMS');
                break;
            case 'notification_template':
                rtnTitle = i18n._('NOTIFICATION TEMPLATES');
                break;
            case 'organization':
                rtnTitle = i18n._('ORGANIZATIONS');
                break;
            case 'job':
                rtnTitle = i18n._('JOBS');
                break;
            case 'custom_inventory_script':
                rtnTitle = i18n._('INVENTORY SCRIPTS');
                break;
            case 'schedule':
                rtnTitle = i18n._('SCHEDULES');
                break;
            case 'host':
                rtnTitle = i18n._('HOSTS');
                break;
            case 'template':
                rtnTitle = i18n._('TEMPLATES');
                break;
            case 'o_auth2_application':
                rtnTitle = i18n._('APPLICATIONS');
                break;
            case 'o_auth2_access_token':
                rtnTitle = i18n._('TOKENS');
                break;
        }

        return rtnTitle;

    };
}

GetTargetTitle.$inject = ['i18n'];
