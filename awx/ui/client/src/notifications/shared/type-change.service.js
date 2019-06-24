/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n',
function (i18n) {
    return{
        getDetailFields: function(type) {
            var obj = {};

            obj.email_required = false;
            obj.slack_required = false;
            obj.grafana_required = false;
            obj.hipchat_required = false;
            obj.pagerduty_required = false;
            obj.irc_required = false;
            obj.twilio_required = false;
            obj.webhook_required = false;
            obj.mattermost_required = false;
            obj.rocketchat_required = false;
            obj.token_required = false;
            obj.port_required = false;
            obj.password_required = false;
            obj.channel_required = false;
            obj.room_required = false;
            switch (type) {
                case 'email':
                    obj.portLabel = ' ' + i18n._('Port');
                    obj.passwordLabel = ' ' + i18n._('Password');
                    obj.email_required = true;
                    obj.port_required = true;
                    obj.password_required = false;
                    break;
                case 'slack':
                    obj.tokenLabel =' ' + i18n._('Token');
                    obj.slack_required = true;
                    obj.token_required = true;
                    obj.channel_required = true;
                    break;
                case 'grafana':
                    obj.grafana_required = true;
                    break;
                case 'hipchat':
                    obj.tokenLabel = ' ' + i18n._('Token');
                    obj.hipchat_required = true;
                    obj.room_required = true;
                    obj.token_required = true;
                    break;
                case 'twilio':
                    obj.twilio_required = true;
                    break;
                case 'webhook':
                    obj.webhook_required = true;
                    obj.passwordLabel = ' ' + i18n._('Basic Auth Password');
                    obj.password_required = false;
                    break;
                case 'mattermost':
                    obj.mattermost_required = true;
                    break;
                case 'rocketchat':
                    obj.rocketchat_required = true;
                    break;
                case 'pagerduty':
                    obj.tokenLabel = ' ' + i18n._('API Token');
                    obj.pagerduty_required = true;
                    obj.token_required = true;
                    break;
                case 'irc':
                    obj.portLabel = ' ' + i18n._('IRC Server Port');
                    obj.passwordLabel = ' ' + i18n._('IRC Server Password');
                    obj.irc_required = true;
                    obj.password_required = false;
                    obj.port_required = true;
                    break;
            }

                // make object an array of tuples
                return Object.keys(obj)
                    .map(i => [i, obj[i]]);
        }
    };


}];
