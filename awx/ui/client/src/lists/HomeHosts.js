/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('HomeHostListDefinition', [])
    .value('HomeHostList', {

        name: 'hosts',
        iterator: 'host',
        selectTitle: 'Add Existing Hosts',
        editTitle: 'Hosts',
        listTitle: 'Hosts',
        index: false,
        hover: true,
        well: true,

        fields: {
            status: {
                label: "",
                iconOnly: true,
                icon: "{{ 'icon-job-' + host.active_failures }}",
                awToolTip: "{{ host.badgeToolTip }}",
                awTipPlacement: "right",
                dataPlacement: "right",
                awPopOver: "{{ host.job_status_html }}",
                ngClick:"bob",
                columnClass: "List-staticColumn--smallStatus",
                searchable: false,
                nosort: true
            },
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-lg-5 col-md-5 col-sm-5 col-xs-8 ellipsis List-staticColumnAdjacent',
                ngClass: "{ 'host-disabled-label': !host.enabled }",
                ngClick: "editHost(host.id)"
            },
            inventory_name: {
                label: 'Inventory',
                sourceModel: 'inventory',
                sourceField: 'name',
                columnClass: 'col-lg-5 col-md-4 col-sm-4 hidden-xs elllipsis',
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

            columnClass: 'col-lg-2 col-md-3 col-sm-3 col-xs-4',

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

        }

    });
