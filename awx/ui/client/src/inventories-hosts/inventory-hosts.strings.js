function InventoryHostsStrings (BaseString) {
    BaseString.call(this, 'inventory-hosts');

    let t = this.t;
    let ns = this['inventory-hosts'];

    ns.filter = {
        GROUP: t('group'),
        GROUPS: t('groups'),
        HOST: t('host'),
        HOSTS: t('hosts'),
        PROMOTE_GROUPS_HOSTS: t('Promote groups and hosts'),
        PROMOTE_GROUP_HOSTS: t('Promote group and hosts'),
        PROMOTE_GROUPS_HOST: t('Promote groups and host'),
        PROMOTE_GROUP_HOST: t('Promote group and host'),
        DELETE_GROUPS_HOSTS: t('Delete groups and hosts'),
        DELETE_GROUP_HOSTS: t('Delete group and hosts'),
        DELETE_GROUPS_HOST: t('Delete groups and host'),
        DELETE_GROUP_HOST: t('Delete group and host'),
        PROMOTE_GROUPS: t('Promote groups'),
        PROMOTE_GROUP: t('Promote group'),
        DELETE_GROUPS: t('Delete groups'),
        DELETE_GROUP: t('Delete group'),
        PROMOTE_HOSTS: t('Promote hosts'),
        PROMOTE_HOST: t('Promote host'),
        DELETE_HOSTS: t('Delete hosts'),
        DELETE_HOST: t('Delete host')
    };

    ns.smartinventories = {
        TOOLTIP: t('Please click the icon to edit the host filter.')
    };
}

InventoryHostsStrings.$inject = ['BaseStringService'];

export default InventoryHostsStrings;
