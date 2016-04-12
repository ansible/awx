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
        name: 'notifier',
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
                    variable: "organizationrequired",
                    init: "true"
                }
            },
            notification_type: {
                label:  'Type',
                type: 'select',
                addRequired: true,
                editRequired: true,
                class: 'NotificationsForm-typeSelect prepend-asterisk',
                ngOptions: 'type.label for type in notification_type_options track by type.value',
                ngChange: 'typeChange()',
                hasSubForm: true
            },
            username: {
                label: 'Username',
                type: 'text',
                awRequiredWhen: {
                    variable: "email_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm'
            },
            use_tls: {
                label: 'Use TLS',
                type: 'checkbox',
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm'
            },
            host: {
                label: 'Host',
                type: 'text',
                awRequiredWhen: {
                    variable: "email_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm'
            },
            sender: {
                label: 'Sender Email',
                type: 'text',
                awRequiredWhen: {
                    variable: "email_required",
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
                    variable: "email_required",
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
                    variable: "password_required" ,
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' || notification_type.value == 'irc' ",
                subForm: 'typeSubForm'
            },
            use_ssl: {
                labelBind: 'sslLabel',
                type: 'checkbox',
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
                    variable: "port_required",
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
                            '<p>For example:<br>engineering<br>\n support<br>\n',
                dataTitle: 'Destination Channels',
                dataPlacement: 'right',
                dataContainer: "body",
                awRequiredWhen: {
                    variable: "channel_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'slack' || notification_type.value == 'hipchat'",
                subForm: 'typeSubForm'
            },
            token: {
                labelBind: 'tokenLabel',
                type: 'sensitive',
                hasShowInputButton: true,
                awRequiredWhen: {
                    variable: "token_required",
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
                    variable: "twilio_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'twilio' ",
                subForm: 'typeSubForm'
            },
            from_number: {
                label: 'Source Phone Number',
                type: 'text',
                awRequiredWhen: {
                    variable: "twilio_required",
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
                            '<p>For example:<br>alias1@email.com<br>\n alias2@email.com<br>\n',
                dataTitle: 'Destination Channels',
                dataPlacement: 'right',
                dataContainer: "body",
                awRequiredWhen: {
                    variable: "twilio_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'twilio' ",
                subForm: 'typeSubForm'
            },
            account_sid: {
                label: 'Account SID',
                type: 'text',
                awRequiredWhen: {
                    variable: "twilio_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'twilio' ",
                subForm: 'typeSubForm'
            },
            subdomain: {
                label: 'Pagerduty subdomain',
                type: 'text',
                awRequiredWhen: {
                    variable: "pagerduty_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'pagerduty' ",
                subForm: 'typeSubForm'
            },
            service_key: {
                label: 'API Service/Integration Key',
                type: 'text',
                awRequiredWhen: {
                    variable: "pagerduty_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'pagerduty' ",
                subForm: 'typeSubForm'
            },
            client_name: {
                label: 'Client Identifier',
                type: 'text',
                awRequiredWhen: {
                    variable: "pagerduty_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'pagerduty' ",
                subForm: 'typeSubForm'
            },
            message_from: {
                label: 'Label to be shown with notification',
                type: 'text',
                awRequiredWhen: {
                    variable: "hipchat_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'hipchat' ",
                subForm: 'typeSubForm'
            },
            api_url: {
                label: 'API URL (e.g: https://mycompany.hiptchat.com)',
                type: 'text',
                awRequiredWhen: {
                    variable: "hipchat_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'hipchat' ",
                subForm: 'typeSubForm'
            },
            color: {
                label: 'Notification Color',
                type: 'text',
                awRequiredWhen: {
                    variable: "hipchat_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'hipchat' ",
                subForm: 'typeSubForm'
            },
            notify: {
                label: 'Notify Channel',
                type: 'text',
                awRequiredWhen: {
                    variable: "hipchat_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'hipchat' ",
                subForm: 'typeSubForm'
            },
            url: {
                label: 'Target URL',
                type: 'text',
                awRequiredWhen: {
                    variable: "webhook_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'webhook' ",
                subForm: 'typeSubForm'
            },
            headers: {
                label: 'HTTP Headers',
                type: 'text',
                awRequiredWhen: {
                    variable: "webhook_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'webhook' ",
                subForm: 'typeSubForm'
            },
            server: {
                label: 'IRC Server Address',
                type: 'text',
                awRequiredWhen: {
                    variable: "irc_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'irc' ",
                subForm: 'typeSubForm'
            },
            nickname: {
                label: 'IRC Nick',
                type: 'text',
                awRequiredWhen: {
                    variable: "irc_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'irc' ",
                subForm: 'typeSubForm'
            },
            targets: {
                label: 'Destination Channels or Users',
                type: 'text',
                awRequiredWhen: {
                    variable: "irc_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'irc' ",
                subForm: 'typeSubForm'
            },

        },

        buttons: { //for now always generates <button> tags
            save: {
                ngClick: 'formSave()', //$scope.function to call on click, optional
                ngDisabled: true //Disable when $pristine or $invalid, optional
            },
            cancel: {
                ngClick: 'formCancel()',
            }
        }
    };
}
