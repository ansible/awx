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
        editTitle: 'Inventory Summary: {{ inventory_name }}',
        showTitle: true,
        well: false,
        index: false,
        hover: true,
        
        fields: {
            name: {
                key: true,
                label: 'Group',
                ngBind: "group.summary_fields.group.name",
                sourceModel: 'group',
                sourceField: 'name',
                ngClick: "\{\{ 'GroupsEdit(' + group.group + ')' \}\}"
                },
            hosts_with_active_failures: {
                label: 'Hosts with<br>Job Failures?',
                ngHref: '/#/inventories/{{ inventory_id }}/hosts{{ group.active_failures_params }}', 
                type: 'badgeCount',
                "class": "{{ 'failures-' + group.has_active_failures }}",
                awToolTip: '# of hosts with job failures. Click to view hosts.',
                dataPlacement: 'bottom',
                searchable: false,
                nosort: true
                },
            has_active_failures: {
                label: 'Hosts have job failures?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true,
                sourceModel: 'group',
                sourceField: 'has_active_failures'
                },
            last_update_failed: {
                label: 'Update failed?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
                },
            status: {
                label: 'Update<br>Status',
                searchType: 'select',
                badgeIcon: 'icon-cloud',
                badgeToolTip: "\{\{ group.status_badge_tooltip \}\}", 
                badgePlacement: 'left',
                badgeClass: "\{\{ 'icon-cloud-' + group.status_badge_class \}\}",
                searchOptions: [
                    { name: "failed", value: "failed" },
                    { name: "never", value: "never updated" },
                    { name: "n/a", value: "none" },
                    { name: "successful", value: "successful" },
                    { name: "updating", value: "updating" }]
                },
            last_updated: {
                label: 'Last<br>Updated',
                searchable: false
                },
            source: {
                label: 'Source',
                searchType: 'select',
                searchOptions: [
                    { name: "Amazon EC2", value: "ec2" },
                    { name: "Local Script", value: "file" },
                    { name: "Manual", value: "" }, 
                    { name: "Rackspace", value: "rackspace" }]
                }
            },

        actions: {
            refresh: {
                awRefresh: true,
                mode: 'all'
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
                dataPlacement: 'left',
                dataContainer: 'body',
                icon: "icon-question-sign",
                mode: 'all',
                'class': 'btn-xs btn-info btn-help pull-right',
                awToolTip: 'Click for help',
                dataTitle: 'Update Status',
                iconSize: 'large'
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
            