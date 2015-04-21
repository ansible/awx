/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  HomeHosts.js
 *
 *  List view object for Hosts data model. Used
 *  on the home tab.
 *
 */



export default
    angular.module('HomeHostListDefinition', [])
    .value('HomeHostList', {

        name: 'hosts',
        iterator: 'host',
        selectTitle: 'Add Existing Hosts',
        editTitle: 'Hosts',
        index: false,
        hover: true,
        well: true,

        fields: {
            status: {
                label: "Status",
                iconOnly: true,
                icon: "{{ 'icon-job-' + host.active_failures }}",
                awToolTip: "{{ host.badgeToolTip }}",
                awTipPlacement: "top",
                dataPlacement: "right",
                awPopOver: "{{ host.job_status_html }}",
                dataTitle: "{{ host.job_status_title }}",
                ngClick:"bob",
                columnClass: "col-md-1 col-sm-2 col-xs-3",
                searchable: false,
                nosort: true
            },
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-lg-4 col-md3 col-sm-3 col-xs-7 ellipsis',
                ngClass: "{ 'host-disabled-label': !host.enabled }",
                ngClick: "editHost(host.id)"
            },
            inventory_name: {
                label: 'Inventory',
                sourceModel: 'inventory',
                sourceField: 'name',
                columnClass: 'col-lg-3 col-md2 col-sm-2 hidden-xs elllipsis',
                linkTo: "{{ '/#/inventories/' + host.inventory }}"
            },
            enabled: {
                label: 'Disabled?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'false',
                searchOnly: true
            },
            has_active_failures: {
                label: 'Has failed jobs?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
            },
            has_inventory_sources: {
                label: 'Has external source?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
            },
            id: {
                label: 'ID',
                searchOnly: true
            }
        },

        fieldActions: {
            /*active_failures: {
                //label: 'Job Status',
                //ngHref: "\{\{'/#/hosts/' + host.id + '/job_host_summaries/?inventory=' + inventory_id \}\}",
                awPopOver: "{{ host.job_status_html }}",
                dataTitle: "{{ host.job_status_title }}",
                awToolTip: "{{ host.badgeToolTip }}",
                awTipPlacement: 'top',
                dataPlacement: 'left',
                iconClass: "{{ 'fa icon-failures-' + host.has_active_failures }}"
            }*/
            edit: {
                label: 'Edit',
                ngClick: "editHost(host.id)",
                icon: 'icon-edit',
                awToolTip: 'Edit host',
                dataPlacement: 'top'
            }
        },

        actions: {
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                mode: 'all',
                awFeature: 'activity_streams'
            }
        }

    });
