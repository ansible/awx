/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        showHeader: false,
        name: 'configuration_jobs_template',
        showActions: true,
        fields: {
            AD_HOC_COMMANDS: {
                type: 'select',
                ngOptions: 'command.label for command in AD_HOC_COMMANDS_options track by command.value',
                reset: 'AD_HOC_COMMANDS',
                multiSelect: true
            },
            AWX_PROOT_BASE_PATH: {
                type: 'text',
                reset: 'AWX_PROOT_BASE_PATH',
            },
            SCHEDULE_MAX_JOBS: {
                type: 'number',
                reset: 'SCHEDULE_MAX_JOBS'
            },
            AWX_PROOT_SHOW_PATHS: {
                type: 'textarea',
                reset: 'AWX_PROOT_SHOW_PATHS',
                rows: 6
            },
            AWX_ANSIBLE_CALLBACK_PLUGINS: {
                type: 'textarea',
                reset: 'AWX_ANSIBLE_CALLBACK_PLUGINS',
                rows: 6
            },
            AWX_PROOT_HIDE_PATHS: {
                type: 'textarea',
                reset: 'AWX_PROOT_HIDE_PATHS',
                rows: 6
            },
            AWX_PROOT_ENABLED: {
                type: 'toggleSwitch',
            },
            DEFAULT_JOB_TIMEOUT: {
                type: 'text',
                reset: 'DEFAULT_JOB_TIMEOUT',
            },
            DEFAULT_INVENTORY_UPDATE_TIMEOUT: {
                type: 'text',
                reset: 'DEFAULT_INVENTORY_UPDATE_TIMEOUT',
            },
            DEFAULT_PROJECT_UPDATE_TIMEOUT: {
                type: 'text',
                reset: 'DEFAULT_PROJECT_UPDATE_TIMEOUT',
            },
            ANSIBLE_FACT_CACHE_TIMEOUT: {
                type: 'text',
                reset: 'ANSIBLE_FACT_CACHE_TIMEOUT',
            },
            PROJECT_UPDATE_VVV: {
                type: 'toggleSwitch',
            },
            AWX_ROLES_ENABLED: {
                type: 'toggleSwitch',
            },
            AWX_COLLECTIONS_ENABLED: {
                type: 'toggleSwitch',
            },
            PRIMARY_GALAXY_URL: {
                type: 'text',
                reset: 'PRIMARY_GALAXY_URL',
            },
            PRIMARY_GALAXY_USERNAME: {
                type: 'text',
                reset: 'PRIMARY_GALAXY_USERNAME',
            },
            PRIMARY_GALAXY_PASSWORD: {
                type: 'sensitive',
                hasShowInputButton: true,
                reset: 'PRIMARY_GALAXY_PASSWORD',
            },
            PRIMARY_GALAXY_TOKEN: {
                type: 'sensitive',
                hasShowInputButton: true,
                reset: 'PRIMARY_GALAXY_TOKEN',
            },
            PRIMARY_GALAXY_AUTH_URL: {
                type: 'text',
                reset: 'PRIMARY_GALAXY_AUTH_URL',
            },
            PUBLIC_GALAXY_ENABLED: {
                type: 'toggleSwitch',
            },
            AWX_TASK_ENV: {
                type: 'textarea',
                reset: 'AWX_TASK_ENV',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth'
            },
            AWX_ISOLATED_HOST_KEY_CHECKING: {
                type: 'toggleSwitch',
            },
            AWX_ISOLATED_CHECK_INTERVAL: {
                type: 'text',
                reset: 'AWX_ISOLATED_CHECK_INTERVAL'
            },
            AWX_ISOLATED_LAUNCH_TIMEOUT: {
                type: 'text',
                reset: 'AWX_ISOLATED_LAUNCH_TIMEOUT'
            },
            AWX_ISOLATED_CONNECTION_TIMEOUT: {
                type: 'text',
                reset: 'AWX_ISOLATED_CONNECTION_TIMEOUT'
            },
            AWX_RESOURCE_PROFILING_ENABLED: {
                type: 'toggleSwitch',
            }
        },
        buttons: {
            reset: {
                ngShow: '!user_is_system_auditor',
                ngClick: 'vm.resetAllConfirm()',
                label: i18n._('Revert all to default'),
                class: 'Form-resetAll'
            },
            cancel: {
                ngClick: 'vm.formCancel()',
            },
            save: {
                ngClick: 'vm.formSave()',
                ngDisabled: true
            }
        }
    };
}];
