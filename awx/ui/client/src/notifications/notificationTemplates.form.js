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

export default ['i18n', function(i18n) {
    return {

        addTitle: i18n._('NEW NOTIFICATION TEMPLATE'),
        editTitle: '{{ name }}',
        name: 'notification_template',
        // I18N for "CREATE NOTIFICATION_TEMPLATE"
        // on /#/notification_templates/add
        breadcrumbName: i18n._('NOTIFICATION TEMPLATE'),
        stateTree: 'notifications',
        basePath: 'notification_templates',
        showActions: true,
        subFormTitles: {
            typeSubForm: i18n._('Type Details'),
        },


        fields: {
            name: {
                label: i18n._('Name'),
                type: 'text',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
                required: true,
                capitalize: false
            },
            description: {
                label: i18n._('Description'),
                type: 'text',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            organization: {
                label: i18n._('Organization'),
                type: 'lookup',
                list: 'OrganizationList',
                basePath: 'organizations',
                sourceModel: 'organization',
                sourceField: 'name',
                required: true,
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            notification_type: {
                label:  i18n._('Type'),
                type: 'select',
                required: true,
                class: 'NotificationsForm-typeSelect',
                ngOptions: 'type.label for type in notification_type_options track by type.value',
                ngChange: 'typeChange()',
                hasSubForm: true,
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            username: {
                label: i18n._('Username'),
                type: 'text',
                ngShow: "notification_type.value == 'email' || notification_type.value == 'webhook' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            password: {
                labelBind: 'passwordLabel',
                type: 'sensitive',
                hasShowInputButton: true,
                awRequiredWhen: {
                    reqExpression: "password_required" ,
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' || notification_type.value == 'irc' || notification_type.value == 'webhook' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            host: {
                label: i18n._('Host'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "email_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            recipients: {
                label: i18n._('Recipient List'),
                type: 'textarea',
                rows: 3,
                awPopOver: i18n._('Enter one email address per line to create a recipient list for this type of notification.'),
                dataTitle: i18n._('Recipient List'),
                dataPlacement: 'right',
                dataContainer: "body",
                awRequiredWhen: {
                    reqExpression: "email_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            sender: {
                label: i18n._('Sender Email'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "email_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
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
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            timeout: {
                label: i18n._('Timeout'),
                type: 'number',
                integer: true,
                default: 30,
                min: 1,
                max: 120,
                spinner: true,
                dataTitle: i18n._('Timeout'),
                dataPlacement: 'right',
                dataContainer: 'body',
                awRequiredWhen: {
                    reqExpression: "email_required",
                    init: "false"
                },
                awPopOver: "<p>" + i18n._("The amount of time (in seconds) before the email notification stops trying to reach the host and times out. Ranges from 1 to 120 seconds.") + "</p>",
                ngShow: "notification_type.value == 'email' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            channels: {
                label: i18n._('Destination Channels'),
                type: 'textarea',
                rows: 3,
                awPopOver: i18n._('Enter one Slack channel per line. The pound symbol (#) is required for channels.'),
                dataTitle: i18n._('Destination Channels'),
                dataPlacement: 'right',
                dataContainer: "body",
                awRequiredWhen: {
                    reqExpression: "channel_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'slack'",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
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
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            account_token: {
                label: i18n._('Account Token'),
                type: 'sensitive',
                hasShowInputButton: true,
                awRequiredWhen: {
                    reqExpression: "twilio_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'twilio' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            from_number: {
                label: i18n._('Source Phone Number'),
                dataTitle: i18n._('Source Phone Number'),
                type: 'text',
                awPopOver: i18n._('Enter the number associated with the "Messaging Service" in Twilio in the format +18005550199.'),
                awRequiredWhen: {
                    reqExpression: "twilio_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'twilio' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            to_numbers: {
                label: i18n._('Destination SMS Number'),
                dataTitle: i18n._('Destination SMS Number'),
                type: 'textarea',
                rows: 3,
                awPopOver: i18n._('Enter one phone number per line to specify where to route SMS messages.'),
                dataPlacement: 'right',
                dataContainer: "body",
                awRequiredWhen: {
                    reqExpression: "twilio_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'twilio' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            account_sid: {
                label: i18n._('Account SID'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "twilio_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'twilio' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            subdomain: {
                label: i18n._('Pagerduty subdomain'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "pagerduty_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'pagerduty' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            service_key: {
                label: i18n._('API Service/Integration Key'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "pagerduty_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'pagerduty' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            client_name: {
                label: i18n._('Client Identifier'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "pagerduty_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'pagerduty' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            grafana_url: {
              label: i18n._('Grafana URL'),
              type: 'text',
              awPopOver: i18n._('The base URL of the Grafana server - the /api/annotations endpoint will be added automatically to the base Grafana URL.'),
              placeholder: 'https://grafana.com',
              dataPlacement: 'right',
              dataContainer: "body",
              awRequiredWhen: {
                  reqExpression: "grafana_required",
                  init: "false"
              },
              ngShow: "notification_type.value == 'grafana' ",
              subForm: 'typeSubForm',
              ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            grafana_key: {
                label: i18n._('Grafana API Key'),
                type: 'sensitive',
                hasShowInputButton: true,
                name: 'grafana_key',
                awRequiredWhen: {
                    reqExpression: "grafana_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'grafana' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            dashboardId: {
              label: i18n._('ID of the Dashboard (optional)'),
              type: 'number',
              integer: true,
              ngShow: "notification_type.value == 'grafana' ",
              subForm: 'typeSubForm',
              ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            panelId: {
              label: i18n._('ID of the Panel (optional)'),
              type: 'number',
              integer: true,
              ngShow: "notification_type.value == 'grafana' ",
              subForm: 'typeSubForm',
              ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            annotation_tags: {
              label: i18n._('Tags for the Annotation (optional)'),
              dataTitle: i18n._('Tags for the Annotation'),
              type: 'textarea',
              name: 'annotation_tags',
              rows: 3,
              placeholder: 'ansible',
              awPopOver: i18n._('Enter one Annotation Tag per line, without commas.'),
              ngShow: "notification_type.value == 'grafana' ",
              subForm: 'typeSubForm',
              ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            grafana_no_verify_ssl: {
                label: i18n._('Disable SSL Verification'),
                type: 'checkbox',
                ngShow: "notification_type.value == 'grafana' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            message_from: {
                label: i18n._('Notification Label'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "hipchat_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'hipchat' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            color: {
                label: i18n._('Notification Color'),
                dataTitle: i18n._('Notification Color'),
                type: 'select',
                ngOptions: 'color.id as color.name for color in hipchatColors',
                awPopOver: i18n._('Specify a notification color. Acceptable colors are: yellow, green, red purple, gray or random.'),
                awRequiredWhen: {
                    reqExpression: "hipchat_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'hipchat' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            notify: {
                label: i18n._('Notify Channel'),
                type: 'checkbox',
                ngShow: "notification_type.value == 'hipchat' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            url: {
                label: i18n._('Target URL'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "webhook_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'webhook' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            disable_ssl_verification: {
                label: i18n._('Disable SSL Verification'),
                type: 'checkbox',
                ngShow: "notification_type.value == 'webhook' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            headers: {
                label: i18n._('HTTP Headers'),
                dataTitle: i18n._('HTTP Headers'),
                type: 'textarea',
                name: 'headers',
                rows: 5,
                'class': 'Form-formGroup--fullWidth',
                awRequiredWhen: {
                    reqExpression: "webhook_required",
                    init: "false"
                },
                awPopOver: i18n._('Specify HTTP Headers in JSON format. Refer to the Ansible Tower documentation for example syntax.'),
                dataPlacement: 'right',
                ngShow: "notification_type.value == 'webhook' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            http_method: {
                label: i18n._('HTTP Method'),
                dataTitle: i18n._('HTTP Method'),
                type: 'select',
                ngOptions: 'choice.id as choice.name for choice in httpMethodChoices',
                default: 'POST',
                awPopOver: i18n._('Specify an HTTP method for the webhook. Acceptable choices are: POST or PUT'),
                awRequiredWhen: {
                    reqExpression: "webhook_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'webhook' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            mattermost_url: {
                label: i18n._('Target URL'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "mattermost_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'mattermost' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            mattermost_username: {
                label: i18n._('Username'),
                type: 'text',
                ngShow: "notification_type.value == 'mattermost' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            mattermost_channel: {
                label: i18n._('Channel'),
                type: 'text',
                ngShow: "notification_type.value == 'mattermost' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            mattermost_icon_url: {
                label: i18n._('Icon URL'),
                type: 'text',
                ngShow: "notification_type.value == 'mattermost' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            mattermost_no_verify_ssl: {
                label: i18n._('Disable SSL Verification'),
                type: 'checkbox',
                ngShow: "notification_type.value == 'mattermost' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            rocketchat_url: {
                label: i18n._('Target URL'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "rocketchat_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'rocketchat' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            rocketchat_username: {
                label: i18n._('Username'),
                type: 'text',
                ngShow: "notification_type.value == 'rocketchat' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            rocketchat_icon_url: {
                label: i18n._('Icon URL'),
                type: 'text',
                ngShow: "notification_type.value == 'rocketchat' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            rocketchat_no_verify_ssl: {
                label: i18n._('Disable SSL Verification'),
                type: 'checkbox',
                ngShow: "notification_type.value == 'rocketchat' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            server: {
                label: i18n._('IRC Server Address'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "irc_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'irc' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            nickname: {
                label: i18n._('IRC Nick'),
                type: 'text',
                awRequiredWhen: {
                    reqExpression: "irc_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'irc' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            targets: {
                label: i18n._('Destination Channels or Users'),
                type: 'textarea',
                rows: 3,
                awPopOver: i18n._('Enter one IRC channel or username per line. The pound symbol (#) for channels, and the at (@) symbol for users, are not required.'),
                dataTitle: i18n._('Destination Channels or Users'),
                dataPlacement: 'right',
                dataContainer: "body",
                awRequiredWhen: {
                    reqExpression: "irc_required",
                    init: "false"
                },
                ngShow: "notification_type.value == 'irc' ",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            use_ssl: {
                label: i18n._('SSL Connection'),
                type: 'checkbox',
                ngShow: "notification_type.value == 'irc'",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            email_options: {
                label: i18n._('Email Options'),
                dataTitle: i18n._('Email Options'),
                defaultText: i18n._('Choose an email option'),
                type: 'select',
                ngOptions: 'type.id as type.name for type in emailOptions',
                ngShow: "notification_type.value == 'email'",
                subForm: 'typeSubForm',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            hex_color: {
                label: i18n._('Notification Color'),
                dataTitle: i18n._('Notification Color'),
                type: 'text',
                subForm: 'typeSubForm',
                ngShow: "notification_type.value == 'slack' ",
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
                awPopOver: i18n._('Specify a notification color. Acceptable colors are hex color code (example: #3af or #789abc) .')
            },
            customize_messages: {
              label: i18n._('Customize messages…'),
              type: 'toggleSwitch',
              toggleSource: 'customize_messages',
              class: 'Form-formGroup--fullWidth',
              ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            custom_message_description: {
                type: 'alertblock',
                ngShow: "customize_messages",
                alertTxt: i18n._('Use custom messages to change the content of notifications ' +
                    'sent when a job starts, succeeds, or fails. Use curly braces to access ' +
                    'information about the job: <code ng-non-bindable>{{ job_friendly_name }}</code>, ' +
                    '<code ng-non-bindable>{{ url }}</code>, or attributes of the job such as ' +
                    '<code ng-non-bindable>{{ job.status }}</code>. You may apply a number of possible ' +
                    'variables in the message. Refer to the ' +
                    '<a href="https://docs.ansible.com/ansible-tower/latest/html/userguide/notifications.html#create-custom-notifications" ' +
                    'target="_blank">Ansible Tower documentation</a> for more details.'),
                closeable: false
            },
            started_message: {
                label: i18n._('Start Message'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && notification_type.value != 'webhook'",
                rows: 2,
                oneLine: 'true',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            started_body: {
                label: i18n._('Start Message Body'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && " +
                  "(notification_type.value == 'email' " +
                  "|| notification_type.value == 'pagerduty' " +
                  "|| notification_type.value == 'webhook')",
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            success_message: {
                label: i18n._('Success Message'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && notification_type.value != 'webhook'",
                rows: 2,
                oneLine: 'true',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            success_body: {
                label: i18n._('Success Message Body'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && " +
                  "(notification_type.value == 'email' " +
                  "|| notification_type.value == 'pagerduty' " +
                  "|| notification_type.value == 'webhook')",
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            error_message: {
                label: i18n._('Error Message'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && notification_type.value != 'webhook'",
                rows: 2,
                oneLine: 'true',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            error_body: {
                label: i18n._('Error Message Body'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && " +
                  "(notification_type.value == 'email' " +
                  "|| notification_type.value == 'pagerduty' " +
                  "|| notification_type.value == 'webhook')",
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            approved_message: {
                label: i18n._('Workflow Approved Message'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && notification_type.value != 'webhook'",
                rows: 2,
                oneLine: 'true',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            approved_body: {
                label: i18n._('Workflow Approved Message Body'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && " +
                  "(notification_type.value == 'email' " +
                  "|| notification_type.value == 'pagerduty' " +
                  "|| notification_type.value == 'webhook')",
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            denied_message: {
                label: i18n._('Workflow Denied Message'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && notification_type.value != 'webhook'",
                rows: 2,
                oneLine: 'true',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            denied_body: {
                label: i18n._('Workflow Denied Message Body'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && " +
                  "(notification_type.value == 'email' " +
                  "|| notification_type.value == 'pagerduty' " +
                  "|| notification_type.value == 'webhook')",
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            running_message: {
                label: i18n._('Workflow Pending Approval Message'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && notification_type.value != 'webhook'",
                rows: 2,
                oneLine: 'true',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            running_body: {
                label: i18n._('Workflow Pending Approval Message Body'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && " +
                  "(notification_type.value == 'email' " +
                  "|| notification_type.value == 'pagerduty' " +
                  "|| notification_type.value == 'webhook')",
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            timed_out_message: {
                label: i18n._('Workflow Timed Out Message'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && notification_type.value != 'webhook'",
                rows: 2,
                oneLine: 'true',
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
            timed_out_body: {
                label: i18n._('Workflow Timed Out Message Body'),
                class: 'Form-formGroup--fullWidth',
                type: 'syntax_highlight',
                mode: 'jinja2',
                default: '',
                ngShow: "customize_messages && " +
                  "(notification_type.value == 'email' " +
                  "|| notification_type.value == 'pagerduty' " +
                  "|| notification_type.value == 'webhook')",
                ngDisabled: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)',
            },
        },

        buttons: { //for now always generates <button> tags
            cancel: {
                ngClick: 'formCancel()',
                ngShow: '(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            close: {
                ngClick: 'formCancel()',
                ngShow: '!(notification_template.summary_fields.user_capabilities.edit || canAdd)'
            },
            save: {
                ngClick: 'formSave()',
                ngShow: '(notification_template.summary_fields.user_capabilities.edit || canAdd)', //$scope.function to call on click, optional
                ngDisabled: true //Disable when $pristine or $invalid, optional
            }
        }
    };
}];
