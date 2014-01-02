/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventorySummary.js 
 *
 *  Summary of groups contained within an inventory
 * 
 */
angular.module('InventoryGroupsDefinition', [])
    .value(
    'InventoryGroups', {

        name: 'groups',
        iterator: 'group',
        editTitle: '{{ inventory_name | capitalize }}',
        showTitle: false,
        well: true,
        index: false,
        hover: true,
        hasChildren: true,
        'class': 'table-condensed',
        
        fields: {
            name: {
                label: 'Group',
                key: true,
                ngClick: "\{\{ 'showHosts(' + group.id + ',' + group.group_id + ')' \}\}",
                ngClass: "group.selected_class",
                hasChildren: true
                },
            status: {
                label: 'Sync Status',
                ngClick: "viewUpdateStatus(\{\{ group.id \}\})",
                searchType: 'select',
                badgeIcon: "\{\{ 'fa icon-cloud-' + group.status_badge_class \}\}",
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
            failed_hosts: {
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
            create: {
                mode: 'all',
                ngClick: "createGroup()",
                ngHide: "groupCreateHide", 
                ngDisabled: 'grpBtnDisabled',
                awToolTip: "Create a new group"
                },
            properties: {
                mode: 'all',
                ngHide: "groupEditHide", 
                ngDisabled: 'grpBtnDisabled',
                awToolTip: "Edit inventory properties" 
                },
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
                },
             help: {
                mode: 'all',
                awToolTip:
                    //"<div style=\"text-align:left;\"><img src=\"/static/img/cow.png\" style=\"width:50px; height:56px; float:left; padding-right:5px;\">" +
                    //"<p>Need help getting started creating your inventory?</p><p>Click here for help.</p></div>",
                    "<div style=\"text-align:left;\"><p>Need help getting started creating your inventory?</p><p>Click here for help.</p></div>",
                ngClick: "showHelp()",
                id: "inventory-summary-help"
                }
            },

        fieldActions: {
            group_update: {
                label: 'Sync',
                ngClick: 'updateGroup(\{\{ group.group_id \}\})',
                awToolTip: "\{\{ group.update_tooltip \}\}",
                ngClass: "group.update_class",
                awToolTip: "Start inventory sync"
                },
            cancel: {
                label: 'Cancel',
                ngClick: "cancelUpdate(\{\{ group.group_id \}\}, '\{\{ group.name \}\}')",
                awToolTip: "\{\{ group.cancel_tooltip \}\}",
                ngClass: "group.cancel_class",
                ngShow: "group.status == 'running' || group.status == 'pending'"
                },
            edit: {
                label: 'Edit',
                ngClick: "editGroup(\{\{ group.group_id \}\})",
                awToolTip: 'Edit group'
                },
            "delete": {
                label: 'Delete',
                ngClick: "deleteGroup(\{\{ group.group_id \}\},'\{\{ group.name \}\}')",
                awToolTip: 'Delete group'
                }
            }
    });
            