function TagService (strings, $filter) {
    this.buildCredentialTag = (credential) => {
        const icon = `${credential.kind}`;
        const link = `/#/credentials/${credential.id}`;
        const tooltip = strings.get('tooltips.CREDENTIAL');
        const value = $filter('sanitize')(credential.name);

        return { icon, link, tooltip, value };
    };
}

TagService.$inject = ['OutputStrings', '$filter'];

export default TagService;
