/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
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
        
        name: 'groups',
        iterator: 'group',
        editTitle: 'Groups',
        index: true,
        hover: true,
        
        fields: {
            name: {
                key: true,
                label: 'Group',
                ngClick: "\{\{ 'GroupsEdit(' + group.id + ')' \}\}",
                columnClass: 'col-lg-3 col-md3 col-sm-2',
                linkTo: "\{\{ '/#/inventories/' + group.inventory + '/groups/?name=' + group.name \}\}"
                },
            inventory_name: {
                label: 'Inventory', 
                sourceModel: 'inventory',
                sourceField: 'name',
                columnClass: 'col-lg-3 col-md3 col-sm-2',
                linkTo: "\{\{ '/#/inventories/' + group.inventory \}\}"
                },
            failed_hosts: {
                label: 'Failed Hosts',
                ngHref: "\{\{ group.failed_hosts_link \}\}",
                badgeIcon: "\{\{ 'icon-failures-' + group.failed_hosts_class \}\}",
                badgeNgHref: "\{\{ group.failed_hosts_link \}\}",
                badgePlacement: 'left',
                badgeToolTip: "\{\{ group.failed_hosts_tip \}\}",
                badgeTipPlacement: 'top',
                awToolTip: "\{\{ group.failed_hosts_tip \}\}",
                dataPlacement: "top",
                searchable: false,
                excludeModal: true,
                sortField: "hosts_with_active_failures"
                },
            status: {
                label: 'Status',
                ngClick: "viewUpdateStatus(\{\{ group.id \}\})",
                searchType: 'select',
                badgeIcon: "\{\{ 'icon-cloud-' + group.status_badge_class \}\}",
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
                },
            last_updated: {
                label: 'Last<br>Updated',
                sourceModel: 'inventory_source',
                sourceField: 'last_updated',
                searchable: false,
                nosort: false
                },
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
                }
            },
        
        actions: {
            stream: {
                'class': "btn-primary btn-xs activity-btn",
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                dataPlacement: "top",
                icon: "icon-comments-alt",
                mode: 'all',
                iconSize: 'large',
                ngShow: "user_is_superuser"
                }
            },

        fieldActions: {
           
            }
        });
