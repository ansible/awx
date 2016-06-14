/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:CustomInventory
 * @description This form is for adding/editing an organization
*/

export default function() {
    return {

        addTitle: 'New Notification Template',
        editTitle: '{{ name }}',
        name: 'notification_template',
        showActions: true,
        subFormTitles: {
            typeSubForm: 'Type Details',
        },

        fields: {
            name: {
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                capitalize: false
            },
            description: {
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false
            },
            organization: {
                label: 'Organization',
                type: 'lookup',
                sourceModel: 'organization',
                sourceField: 'name',
                ngClick: 'lookUpOrganization()',
                awRequiredWhen: {
                    reqExpression: "organizationrequired",
                    init: "true"
                }
            },
            notification_type: {
                label:  'Type',
                type: 'select',
                addRequired: true,
                editRequired: true,
                class: 'NotificationsForm-typeSelect',
                ngOptions: 'type.label for type in notification_type_options track by type.value',
                ngChange: 'typeChange()',
                hasSubForm: true
            },
            username: {
                label: 'Username',
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "email_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm'
            },

            host: {
                label: 'Host',
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "email_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm'
            },
            sender: {
                label: 'Sender Email',
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "email_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm'
            },
            recipients: {
                label: 'Recipient List',
                type: 'textarea',
                rows: 3,
                awPopOver: '<p>Type an option on each line.</p>'+
                            '<p>For example:<br>alias1@email.com<br>\n alias2@email.com<br>\n',
                dataTitle: 'Recipient List',
                dataPlacement: 'right',
                dataContainer: "body",
                awRequiredWhen: {
                    reqExpression: "email_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm'
            },
            password: {
                labelBind: 'passwordLabel',
                type: 'sensitive',
                hasShowInputButton: true,
                awRequiredWhen: {
                    reqExpression: "password_required" ,
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' || notification_type.value == 'irc' ",
                subForm: 'typeSubForm'
            },
            port: {
                labelBind: 'portLabel',
                type: 'number',
                integer: true,
                spinner: true,
                'class': "input-small",
                min: 0,
                awRequiredWhen: {
                    reqExpression: "port_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' || notification_type.value == 'irc'",
                subForm: 'typeSubForm'
            },
            channels: {
                label: 'Destination Channels',
                type: 'textarea',
                rows: 3,
                awPopOver: '<p>Type an option on each line. The pound symbol (#) is not required.</p>'+
                            '<p>For example:<br>engineering<br>\n #support<br>\n',
                dataTitle: 'Destination Channels',
                dataPlacement: 'right',
                dataContainer: "body",
                awRequiredWhen: {
                    reqExpression: "channel_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'slack'",
                subForm: 'typeSubForm'
            },
            rooms: {
                label: 'Destination Channels',
                type: 'textarea',
                rows: 3,
                awPopOver: '<p>Type an option on each line. The pound symbol (#) is not required.</p>'+
                            '<p>For example:<br>engineering<br>\n #support<br>\n',
                dataTitle: 'Destination Channels',
                dataPlacement: 'right',
                dataContainer: "body",
                awRequiredWhen: {
                    reqExpression: "room_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'hipchat'",
                subForm: 'typeSubForm'
            },
            token: {
                labelBind: 'tokenLabel',
                type: 'sensitive',
                hasShowInputButton: true,
                awRequiredWhen: {
                    reqExpression: "token_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'slack' || notification_type.value == 'pagerduty' || notification_type.value == 'hipchat'",
                subForm: 'typeSubForm'
            },
            account_token: {
                label: 'Account Token',
                type: 'sensitive',
                hasShowInputButton: true,
                awRequiredWhen: {
                    reqExpression: "twilio_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'twilio' ",
                subForm: 'typeSubForm'
            },
            from_number: {
                label: 'Source Phone Number',
                type: 'text',
                awPopOver: '<p>Number associated with the "Messaging Service" in Twilio.</p>'+
                            '<p>This must be of the form <code>+18005550199</code>.</p>',
                awRequiredWhen: {
                    reqExpression: "twilio_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'twilio' ",
                subForm: 'typeSubForm'
            },
            to_numbers: {
                label: 'Destination SMS Number',
                type: 'textarea',
                rows: 3,
                awPopOver: '<p>Type an option on each line.</p>'+
                            '<p>For example:<br><code>+12125552368</code><br>\n<code>+19105556162</code><br>\n',
                dataTitle: 'Destination SMS Number',
                dataPlacement: 'right',
                dataContainer: "body",
                awRequiredWhen: {
                    reqExpression: "twilio_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'twilio' ",
                subForm: 'typeSubForm'
            },
            account_sid: {
                label: 'Account SID',
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "twilio_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'twilio' ",
                subForm: 'typeSubForm'
            },
            subdomain: {
                label: 'Pagerduty subdomain',
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "pagerduty_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'pagerduty' ",
                subForm: 'typeSubForm'
            },
            service_key: {
                label: 'API Service/Integration Key',
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "pagerduty_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'pagerduty' ",
                subForm: 'typeSubForm'
            },
            client_name: {
                label: 'Client Identifier',
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "pagerduty_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'pagerduty' ",
                subForm: 'typeSubForm'
            },
            message_from: {
                label: 'Label to be shown with notification',
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "hipchat_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'hipchat' ",
                subForm: 'typeSubForm'
            },
            api_url: {
                label: 'API URL',
                type: 'text',
                placeholder: 'https://mycompany.hipchat.com',
                awRequiredWhen: {
                    reqExpression: "hipchat_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'hipchat' ",
                subForm: 'typeSubForm'
            },
            color: {
                label: 'Notification Color',
                type: 'text',
                awPopOver: '<p>Color can be one of <code>yellow</code>, <code>green</code>, <code>red</code>, ' +
                           '<code>purple</code>, <code>gray</code>, or <code>random</code>.\n',
                awRequiredWhen: {
                    reqExpression: "hipchat_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'hipchat' ",
                subForm: 'typeSubForm'
            },
            notify: {
                label: 'Notify Channel',
                type: 'checkbox',
                ngShow: "notification_type.value == 'hipchat' ",
                subForm: 'typeSubForm'
            },
            url: {
                label: 'Target URL',
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "webhook_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'webhook' ",
                subForm: 'typeSubForm'
            },
            headers: {
                label: 'HTTP Headers',
                type: 'textarea',
                rows: 5,
                'class': 'Form-formGroup--fullWidth',
                awRequiredWhen: {
                    reqExpression: "webhook_required",
                    init: "false"
                },
                awPopOver: '<p>Specify HTTP Headers in JSON format</p>' +
                           '<p>For example:<br><pre>\n' +
                           '{\n' +
                           '  "X-Auth-Token": "828jf0",\n' +
                           '  "X-Ansible": "Is great!"\n' +
                           '}\n' +
                           '</pre></p>',
                dataPlacement: 'right',
                ngShow: "notification_type.value == 'webhook' ",
                subForm: 'typeSubForm'
            },
            server: {
                label: 'IRC Server Address',
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "irc_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'irc' ",
                subForm: 'typeSubForm'
            },
            nickname: {
                label: 'IRC Nick',
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "irc_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'irc' ",
                subForm: 'typeSubForm'
            },
            targets: {
                label: 'Destination Channels or Users',
                type: 'textarea',
                rows: 3,
                awPopOver: '<p>Type an option on each line. The pound symbol (#) is not required.</p>'+
                            '<p>For example:<br>#support or support<br>\n @username or username<br>\n',
                dataTitle: 'Destination Channels',
                dataPlacement: 'right',
                dataContainer: "body",
                awRequiredWhen: {
                    reqExpression: "irc_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'irc' ",
                subForm: 'typeSubForm'
            },
            use_tls: {
                label: 'Use TLS',
                type: 'checkbox',
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm'
            },
            use_ssl: {
                labelBind: 'sslLabel',
                type: 'checkbox',
                ngShow: "notification_type.value == 'email' || notification_type.value == 'irc' ",
                subForm: 'typeSubForm'
            },

        },

        buttons: { //for now always generates <button> tags
            cancel: {
                ngClick: 'formCancel()',
            },
            save: {
                ngClick: 'formSave()', //$scope.function to call on click, optional
                ngDisabled: true //Disable when $pristine or $invalid, optional
            }
        }
    };
}
