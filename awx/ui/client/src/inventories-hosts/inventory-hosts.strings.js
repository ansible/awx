function InventoryHostsStrings (BaseString) {
    BaseString.call(this, 'inventory-hosts');

    let t = this.t;
    let ns = this['inventory-hosts'];

    ns.deletegroup = {
        GROUP: count => t.p(count, 'group', 'groups'),
        HOST: count => t.p(count, 'host', 'hosts'),
        PROMOTE_GROUPS_AND_HOSTS: data => t.s('Promote {{ group }} and {{ host }}', {
            group: this.get('deletegroup.GROUP', data.groups),
            host: this.get('deletegroup.HOST', data.hosts)
        }),
        DELETE_GROUPS_AND_HOSTS: data => t.s('Delete {{ group }} and {{ host }}', {
            group: this.get('deletegroup.GROUP', data.groups),
            host: this.get('deletegroup.HOST', data.hosts)
        }),
        PROMOTE_GROUP: count => t.p(count, 'Promote group', 'Promote groups'),
        DELETE_GROUP: count => t.p(count, 'Delete group', 'Delete groups'),
        PROMOTE_HOST: count => t.p(count, 'Promote host', 'Promote hosts'),
        DELETE_HOST: count => t.p(count, 'Delete host', 'Delete hosts'),
    };

    ns.inventory = {
        EDIT_HOST: t.s('Edit host'),
        VIEW_HOST: t.s('View host'),
        VIEW_INSIGHTS: t.s('View Insights Data')
    };

    ns.hostList = {
        DISABLED_TOGGLE_TOOLTIP: () => t.s('{{ str1 }}</p><p>{{ str2 }}</p>', {
            str1: t.s('Indicates if a host is available and should be included in running jobs.'), 
            str2: t.s('For hosts that are part of an external inventory, this may be reset by the inventory sync process.')
        })
    };

    ns.smartinventories = {
        hostfilter: {
            MISSING_ORG: t.s('Please select an organization before editing the host filter.'),
            INSTRUCTIONS: t.s('Please click the icon to edit the host filter.'),
            MISSING_PERMISSIONS: t.s('You do not have sufficient permissions to edit the host filter.'),
            OPEN: t.s('Open host filter')
        }
    };

    ns.smartinventorybutton = {
        DISABLED_INSTRUCTIONS: t.s("Please enter at least one search term to create a new Smart Inventory."),
        ENABLED_INSTRUCTIONS: t.s("Create a new Smart Inventory from search results.<br /><br />Note: changing the organization of the Smart Inventory could change the hosts included in the Smart Inventory.")
    };

    ns.insights = {
        VIEW: t.s("View Insights")
    };
}

InventoryHostsStrings.$inject = ['BaseStringService'];

export default InventoryHostsStrings;
