function TagService (strings, $filter) {
    this.buildCredentialTag = (credential) => {
        const icon = `${credential.kind}`;
        const link = `/#/credentials/${credential.id}`;
        const tooltip = strings.get('tooltips.VIEW_THE_CREDENTIAL');
        const value = $filter('sanitize')(credential.name);

        return { icon, link, tooltip, value };
    };
    this.buildTag = (tag) => {
        const value = $filter('sanitize')(tag);

        return { value };
    };
}

TagService.$inject = ['ComponentsStrings', '$filter'];

export default TagService;
