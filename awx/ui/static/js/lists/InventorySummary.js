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
                noLink: true,
                ngBind: "group.summary_fields.group.name",
                sourceModel: 'group',
                sourceField: 'name',
                badges: [
                    { //Active Failures
                      icon: "\{\{ 'icon-failures-' + group.summary_fields.group.has_active_failures \}\}",
                      toolTip: 'Indicates if inventory contains hosts with active failures',
                      toolTipPlacement: 'bottom'
                      },
                    { //Cloud Status
                      icon: "\{\{ 'icon-cloud-' + group.status_class \}\}",
                      toolTip: 'Indicates status of inventory update process',
                      toolTipPlacement: 'bottom'
                      }]
                },
            failures: {
                label: 'Active<br>Failures',
                ngBind: "group.summary_fields.group.hosts_with_active_failures",
                sourceModel: 'group',
                sourceField: 'hosts_with_active_failures',
                searchField: 'group__has_active_failures',
                searchType: 'boolean',
                searchOptions: [{ name: "yes", value: 1 }, { name: "no", value: 0 }]
                },
            source: {
                label: 'Source',
                searchType: 'select',
                searchOptions: [
                    { name: "Amazon EC2", value: "ec2" },
                    { name: "Local Script", value: "file" },
                    { name: "Manual", value: "" }, 
                    { name: "Rackspace", value: "rackspace" }]
                },
            last_updated: {
                label: 'Last<br>Updated',
                searchable: false
                },
            status: {
                label: 'Update<br>Status',
                searchType: 'select',
                searchOptions: [
                    { name: "failed", value: "failed" },
                    { name: "never", value: "never updated" },
                    { name: "n/a", value: "none" },
                    { name: "successful", value: "successful" },
                    { name: "updating", value: "updating" }]
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
            