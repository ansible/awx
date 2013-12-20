/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
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
        class: 'table-condensed',
        
        fields: {
            name: {
                label: 'Group',
                key: true,
                ngClick: "\{\{ 'GroupsEdit(' + group.id + ')' \}\}",
                //ngClass: "\{\{ 'level' + group.level \}\}",
                hasChildren: true
                },
            status: {
                label: 'Sync Status',
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
                label: 'Add',
                mode: 'all',
                icon: 'icon-plus',
                ngClick: "createGroup()",
                ngHide: "groupCreateHide", 
                ngDisabled: 'grpBtnDisabled',
                awToolTip: "Create a new group", 
                dataPlacement: 'top'
                },
            edit: {
                label: 'Edit',
                mode: 'all',
                icon: 'icon-wrench',
                'class': "btn-sm", 
                ngHide: "groupEditHide", 
                ngDisabled: 'grpBtnDisabled',
                awToolTip: "Edit inventory properties", 
                dataPlacement: 'top'
                },
            refresh: {
                label: 'Refresh',
                dataPlacement: 'top',
                icon: "icon-refresh",
                mode: 'all',
                'class': 'btn-sm',
                awToolTip: "Refresh the page",
                ngClick: "refresh()"
                },
            stream: {
                label: 'Activity',
                'class': "activity-btn",
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                dataPlacement: "top",
                icon: "icon-comments-alt",
                mode: 'all',
                ngShow: "user_is_superuser"
                },
             help: {
                label: 'Help',
                dataPlacement: 'top',
                icon: "icon-question-sign",
                mode: 'all',
                'class': 'btn-sm btn-help',
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
                icon: 'icon-cloud-download',
                "class": 'btn-xs btn-primary',
                ngClick: 'updateGroup(\{\{ group.id \}\})',
                awToolTip: "\{\{ group.update_tooltip \}\}",
                ngClass: "group.update_class",
                awToolTip: "Start inventory sync"
                },
            cancel: {
                label: 'Cancel',
                icon: 'icon-minus-sign',
                ngClick: "cancelUpdate(\{\{ group.id \}\}, '\{\{ group.name \}\}')",
                "class": 'btn-xs btn-primary',
                awToolTip: "\{\{ group.cancel_tooltip \}\}",
                ngClass: "group.cancel_class",
                ngShow: "group.status == 'running' || group.status == 'pending'"
                },
             edit: {
                label: 'Edit',
                ngClick: "editGroup(\{\{ group.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-xs btn-primary',
                awToolTip: 'Edit group'
                },
            "delete": {
                label: 'Delete',
                ngClick: "deleteGroup(\{\{ group.id \}\},'\{\{ group.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-xs btn-primary',
                awToolTip: 'Delete group'
                }
            }
    });
            