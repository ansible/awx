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

    ns.smartinventories = {
        hostfilter: {
            MISSING_ORG: t.s('Please select an organization before editing the host filter.'),
            INSTRUCTIONS: t.s('Please click the icon to edit the host filter.'),
            MISSING_PERMISSIONS: t.s('You do not have sufficient permissions to edit the host filter.')
        }
    };
}

InventoryHostsStrings.$inject = ['BaseStringService'];

export default InventoryHostsStrings;
