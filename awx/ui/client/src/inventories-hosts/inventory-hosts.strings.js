function InventoryHostsStrings (BaseString) {
    BaseString.call(this, 'inventoryhosts');

    let t = this.t;
    let ns = this.inventoryhosts;

    ns.filter = {
        GROUP: t('group'),
        GROUPS: t('groups'),
        HOST: t('host'),
        HOSTS: t('hosts'),
        PROMOTEGROUPSHOSTS: t('Promote groups and hosts'),
        PROMOTEGROUPHOSTS: t('Promote group and hosts'),
        PROMOTEGROUPSHOST: t('Promote groups and host'),
        PROMOTEGROUPHOST: t('Promote group and host'),
        DELETEGROUPSHOSTS: t('Delete groups and hosts'),
        DELETEGROUPHOSTS: t('Delete group and hosts'),
        DELETEGROUPSHOST: t('Delete groups and host'),
        DELETEGROUPHOST: t('Delete group and host'),
        PROMOTEGROUPS: t('Promote groups'),
        PROMOTEGROUP: t('Promote group'),
        DELETEGROUPS: t('Delete groups'),
        DELETEGROUP: t('Delete group'),
        PROMOTEHOSTS: t('Promote hosts'),
        PROMOTEHOST: t('Promote host'),
        DELETEHOSTS: t('Delete hosts'),
        DELETEHOST: t('Delete host')
    };
}

InventoryHostsStrings.$inject = ['BaseStringService'];

export default InventoryHostsStrings;
