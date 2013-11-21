/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  InventorySummary.js 
 *
 *  Summary of groups contained within an inventory
 * 
 */
angular.module('InventorySummaryDefinition', [])
    .value(
    'InventorySummary', {

        name: 'groups',
        iterator: 'group',
        editTitle: '{{ inventory_name | capitalize }}',
        showTitle: true,
        well: true,
        index: false,
        hover: true,
        
        fields: {
            name: {
                key: true,
                label: 'Group',
                ngClick: "\{\{ 'GroupsEdit(' + group.id + ')' \}\}",
                columnClass: 'col-lg-3 col-md3 col-sm-2'
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
            create: {
                label: 'Create New',
                mode: 'all',
                icon: 'icon-plus',
                'class': "btn-success btn-xs", 
                ngClick: "createGroup()",
                ngHide: "groupCreateHide", 
                ngDisabled: 'grpBtnDisabled',
                awToolTip: "Create a new top-level group", 
                dataPlacement: 'top'
                },
            help: {
                dataPlacement: 'top',
                icon: "icon-question-sign",
                mode: 'all',
                'class': 'btn-xs btn-info btn-help',
                awToolTip:
                    //"<div style=\"text-align:left;\"><img src=\"/static/img/cow.png\" style=\"width:50px; height:56px; float:left; padding-right:5px;\">" +
                    //"<p>Need help getting started creating your inventory?</p><p>Click here for help.</p></div>",
                    "<div style=\"text-align:left;\"><p>Need help getting started creating your inventory?</p><p>Click here for help.</p></div>",
                iconSize: 'large',
                ngClick: "showHelp()",
                id: "inventory-summary-help"
                },
            refresh: {
                dataPlacement: 'top',
                icon: "icon-refresh",
                mode: 'all',
                'class': 'btn-xs btn-primary',
                awToolTip: "Refresh the page",
                ngClick: "refresh()",
                iconSize: 'large'
                },
            reset: {
                dataPlacement: 'top',
                icon: "icon-undo",
                mode: 'all',
                'class': 'btn-xs btn-primary',
                awToolTip: "Reset the search filter",
                ngClick: "resetSearch()",
                iconSize: 'large'
                },
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
            group_update: {
                label: 'Update',
                icon: 'icon-cloud-download',
                "class": 'btn-xs btn-success',
                ngClick: 'updateGroup(\{\{ group.id \}\})',
                awToolTip: "\{\{ group.update_tooltip \}\}",
                ngClass: "group.update_class"
                },
            cancel: {
                label: 'Cancel',
                icon: 'icon-minus-sign',
                ngClick: "cancelUpdate(\{\{ group.id \}\}, '\{\{ group.name \}\}')",
                "class": 'btn-danger btn-xs delete-btn',
                awToolTip: "\{\{ group.cancel_tooltip \}\}",
                ngClass: "group.cancel_class"
                }
            }
    });
            