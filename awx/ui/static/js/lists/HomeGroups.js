/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  HomeGroups.js 
 *
 *  List view object for Group data model. Used
 *  on the home tab.
 *
 */
angular.module('HomeGroupListDefinition', [])
    .value(
    'HomeGroupList', {
        
        name: 'home_groups',
        iterator: 'group',
        editTitle: 'Groups',
        index: true,
        hover: true,
        well: true,

        fields: {
            name: {
                key: true,
                label: 'Group',
                ngClick: "editGroup(group.id, group.inventory)",
                columnClass: 'col-lg-4 col-md3 col-sm-3 col-xs-6 ellipsis'
                },
            inventory_name: {
                label: 'Inventory', 
                sourceModel: 'inventory',
                sourceField: 'name',
                columnClass: 'col-lg-3 col-md2 col-sm-2 hidden-xs elllipsis',
                linkTo: "\{\{ '/#/inventories/' + group.inventory + '/' \}\}"
                },
            /*failed_hosts: {
                label: 'Failed Hosts',
                ngHref: "\{\{ group.failed_hosts_link \}\}",
                badgeIcon: "\{\{ 'fa icon-failures-' + group.failed_hosts_class \}\}",
                badgeNgHref: "\{\{ group.failed_hosts_link \}\}",
                badgePlacement: 'left',
                badgeToolTip: "\{\{ group.failed_hosts_tip \}\}",
                badgeTipPlacement: 'top',
                awToolTip: "\{\{ group.failed_hosts_tip \}\}",
                dataPlacement: "top",
                searchable: false,
                excludeModal: true,
                sortField: "hosts_with_active_failures"
                },*/
            /*status: {
                label: 'Status',
                ngClick: "viewUpdateStatus(\{\{ group.id \}\})",
                searchType: 'select',
                badgeIcon: "\{\{ 'fa fa-cloud ' + group.status_badge_class \}\}",
                badgeToolTip: "\{\{ group.status_badge_tooltip \}\}",
                awToolTip: "\{\{ group.status_badge_tooltip \}\}",
                dataPlacement: 'top',
                badgeTipPlacement: 'top',
                badgePlacement: 'left',
                searchOptions: [
                    { name: "failed", value: "failed" },
                    { name: "never", value: "never updated" },
                    { name: "n/a", value: "none" },
                    { name: "successful", value: "successful" },
                    { name: "updating", value: "updating" }],
                sourceModel: 'inventory_source',
                sourceField: 'status'
                },*/
            /*last_updated: {
                label: 'Last<br>Updated',
                sourceModel: 'inventory_source',
                sourceField: 'last_updated',
                searchable: false,
                nosort: false
                },*/
            source: {
                label: 'Source',
                searchType: 'select',
                searchOptions: [
                    { name: "ec2", value: "ec2" },
                    { name: "none", value: "" },
                    { name: "rax", value: "rax" }],
                sourceModel: 'inventory_source',
                sourceField: 'source',
                searchOnly: true
                },
            has_external_source: {
                label: 'Has external source?', 
                searchType: 'in', 
                searchValue: 'ec2,rax',
                searchOnly: true,
                sourceModel: 'inventory_source',
                sourceField: 'source'
                },
            has_active_failures: {
                label: 'Has failed hosts?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
                },
            last_update_failed: {
                label: 'Update failed?',
                searchType: 'select',
                searchSingleValue: true,
                searchValue: 'failed',
                searchOnly: true,
                sourceModel: 'inventory_source',
                sourceField: 'status'
                },
            id: {
                label: 'ID',
                searchOnly: true
                }
            },

        fieldActions: {
            sync_status: {
                mode: 'all',
                ngClick: "viewUpdateStatus(group.id, group.group_id)",
                awToolTip: "\{\{ group.status_tooltip \}\}",
                ngClass: "group.status_class",
                dataPlacement: "top"
                },
            failed_hosts: {
                mode: 'all',
                awToolTip: "{{ group.hosts_status_tip }}",
                dataPlacement: "top",
                ngHref: "/#/inventories/{{ group.inventory }}/",
                iconClass: "{{ 'fa icon-failures-' + group.hosts_status_class }}"
                },
            group_update: {
                //label: 'Sync',
                mode: 'all',
                ngClick: 'updateGroup(\{\{ group.id \}\})',
                awToolTip: "\{\{ group.launch_tooltip \}\}",
                ngShow: "(group.status !== 'running' && group.status !== 'pending' && group.status !== 'updating')",
                ngClass: "group.launch_class",
                dataPlacement: "top"
                },
            cancel: {
                //label: 'Cancel',
                mode: 'all',
                ngClick: "cancelUpdate(\{\{ group.id \}\})",
                awToolTip: "Cancel sync process",
                'class': 'red-txt',
                ngShow: "(group.status == 'running' || group.status == 'pending' || group.status == 'updating')",
                dataPlacement: "top"
                },
            edit: {
                label: 'Edit',
                mode: 'all',
                ngClick: "editGroup(group.id)",
                awToolTip: 'Edit group',
                dataPlacement: "top"
                }
            },
        
        actions: {
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refresh()"
                },
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                mode: 'all',
                ngShow: "user_is_superuser"
                }
            }

        });
