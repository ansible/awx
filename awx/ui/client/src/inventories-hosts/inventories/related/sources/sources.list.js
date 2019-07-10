/*************************************************
 * Copyright (c) 2017  Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default ['i18n', function(i18n) {
     return {
        name: 'inventory_sources',
        iterator: 'inventory_source',
        editTitle: '{{ inventory_source.name }}',
        well: true,
        wellOverride: true,
        index: false,
        hover: true,
        trackBy: 'inventory_source.id',
        basePath:  'api/v2/inventories/{{$stateParams.inventory_id}}/inventory_sources/',
        layoutClass: 'List-staticColumnLayout--statusOrCheckbox',
        staticColumns: [
            {
                field: 'sync_status',
                content: {
                    label: '',
                    nosort: true,
                    mode: 'all',
                    iconOnly: true,
                    ngClick: 'viewUpdateStatus(inventory_source.id)',
                    awToolTip: "{{ inventory_source.status_tooltip }}",
                    dataTipWatch: "inventory_source.status_tooltip",
                    icon: "{{ 'fa icon-cloud-' + inventory_source.status_class }}",
                    ngClass: "inventory_source.status_class",
                    dataPlacement: "top",
                }
            }
        ],

        fields: {
            name: {
                label: i18n._('Sources'),
                key: true,
                uiSref: "inventories.edit.inventory_sources.edit({inventory_source_id:inventory_source.id})",
                columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-4',
            },
            source: {
                label: i18n._('Type'),
                ngBind: 'inventory_source.source_label',
                columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-4'
            }
        },

        actions: {
            refresh: {
                mode: 'all',
                awToolTip: i18n._("Refresh the page"),
                ngClick: "refreshGroups()",
                ngShow: "socketStatus == 'error'",
                actionClass: 'btn List-buttonDefault',
                buttonContent: i18n._('REFRESH')
            },
            sync_all: {
                mode: 'all',
                awToolTip: i18n._("Sync all inventory sources"),
                ngClick: "syncAllSources()",
                ngShow: "showSyncAll",
                actionClass: 'btn List-buttonDefault',
                buttonContent: i18n._('SYNC ALL'),
                dataPlacement: "top"
            },
            create: {
                mode: 'all',
                ngClick: "createSource()",
                awToolTip: i18n._("Create a new source"),
                actionClass: 'at-Button--add',
                actionId: 'button-add',
                ngShow: 'canAdd',
                dataPlacement: "top",
            }
        },

        fieldActions: {

            columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-4 text-right',

            edit: {
                mode: 'all',
                ngClick: "editSource(inventory_source.id)",
                awToolTip: i18n._('Edit source'),
                dataPlacement: "top",
                ngShow: "inventory_source.summary_fields.user_capabilities.edit"
            },
            source_update: {
                mode: 'all',
                ngClick: 'updateSource(inventory_source)',
                awToolTip: "{{ inventory_source.launch_tooltip }}",
                dataTipWatch: "inventory_source.launch_tooltip",
                ngShow: "(inventory_source.status !== 'running' && inventory_source.status " +
                    "!== 'pending' && inventory_source.status !== 'updating') && inventory_source.summary_fields.user_capabilities.start",
                ngClass: "inventory_source.launch_class",
                dataPlacement: "top",
            },
            cancel: {
                mode: 'all',
                ngClick: "cancelUpdate(inventory_source.id)",
                awToolTip: i18n._("Cancel sync process"),
                'class': 'red-txt',
                ngShow: "(inventory_source.status == 'running' || inventory_source.status == 'pending' " +
                    "|| inventory_source.status == 'updating') && inventory_source.summary_fields.user_capabilities.start",
                dataPlacement: "top",
                iconClass: "fa fa-minus-circle"
            },
            view: {
                mode: 'all',
                ngClick: "editSource(inventory_source.id)",
                awToolTip: i18n._('View source'),
                dataPlacement: "top",
                ngShow: "!inventory_source.summary_fields.user_capabilities.edit"
            },
            "delete": {
                mode: 'all',
                ngClick: "deleteSource(inventory_source)",
                awToolTip: i18n._('Delete source'),
                dataPlacement: "top",
                ngShow: "inventory_source.summary_fields.user_capabilities.delete"
            }
        }
    };
}];
