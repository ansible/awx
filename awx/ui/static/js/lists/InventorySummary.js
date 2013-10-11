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
        editTitle: '{{ inventory_name }}',
        showTitle: true,
        well: true,
        index: false,
        hover: true,
        
        fields: {
            name: {
                key: true,
                label: 'Group',
                ngClick: "\{\{ 'GroupsEdit(' + group.id + ')' \}\}"
                },
            hosts_with_active_failures: {
                label: 'Hosts with<br>Job Failures?',
                ngHref: '/#/inventories/{{ inventory_id }}/hosts{{ group.active_failures_params }}', 
                type: 'badgeCount',
                "class": "{{ 'failures-' + group.has_active_failures }}",
                awToolTip: '# of hosts with job failures. Click to view hosts.',
                dataPlacement: 'top',
                searchable: false,
                nosort: false
                },
            status: {
                label: 'Update<br>Status',
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
                    { name: "rackspace", value: "rackspace" }],
                sourceModel: 'inventory_source',
                sourceField: 'source'
                },
            has_external_source: {
                label: 'Has external source?', 
                searchType: 'in', 
                searchValue: 'ec2,rackspace',
                searchOnly: true,
                sourceModel: 'inventory_source',
                sourceField: 'source'
                },
            has_active_failures: {
                label: 'Hosts have job failures?',
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
                awPopOver: 
                    "<dl>\n" +
                    "<dt>failed</dt><dd>Errors were encountered with the most recent inventory update.</dd>\n" +
                    "<dt>n/a</dt><dd>The group is not configured for inventory update.</dd>\n" +
                    "<dt>never</dt><dd>The inventory update has never run for the group.</dd>\n" +
                    "<dt>successful</dt><dd>The most recent inventory update ran to completion without incident.</dd>\n" +
                    "<dt>updating</dt><dd>The inventory update is currently running.</dd>\n" +
                    "</dl>\n",
                dataPlacement: 'top',
                dataContainer: 'body',
                icon: "icon-question-sign",
                mode: 'all',
                'class': 'btn-xs btn-info btn-help',
                awToolTip: 'Click for help',
                dataTitle: 'Update Status',
                iconSize: 'large'
                },
            refresh: {
                awRefresh: true,
                mode: 'all'
                }
            },

        fieldActions: {
            group_update: {
                label: 'Update',
                icon: 'icon-cloud-download',
                "class": 'btn-xs btn-success',
                ngClick: 'updateGroup(\{\{ group.id \}\})',
                awToolTip: 'Perform an update on this group'     
                }
            }
    });
            