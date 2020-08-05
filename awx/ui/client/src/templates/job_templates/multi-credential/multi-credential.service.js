function MultiCredentialService (Rest, ProcessErrors, $q, GetBasePath)  {

    const handleError = (method, resource, permitted = []) => {
        return ({ data, status }) => {
            if (permitted.indexOf(status) > -1) {
                return { data, status };
            }
            const hdr = 'Error!';
            const msg = `${resource} request failed. ${method} returned status: ${status}`;
            return ProcessErrors(null, data, status, null, { hdr, msg });
        };
    };

    const associate = ({ related }, id) => {
        Rest.setUrl(related.credentials);
        return Rest
            .post({ id })
            .then(({ data }) => data.results)
            .catch(handleError('POST', 'credential association'));
    };

    const disassociate = ({ related }, id) => {
        Rest.setUrl(related.credentials);
        return Rest
            .post({ id, disassociate: true })
            .catch(handleError('POST', 'credential disassociation'));
    };

    this.saveRelated = ({ related }, credentials) => {
        Rest.setUrl(related.credentials);
        return Rest
            .get()
            .then(({ data }) => {
                const currentlyAssociated = data.results.map(c => c.id);
                const selected = credentials.map(c => c.id);

                const disassociationPromises = currentlyAssociated
                    .filter(id => selected.indexOf(id) < 0)
                    .map(id => disassociate({ related }, id));

                return $q.all(disassociationPromises).then(() => {
                    _.each(selected.filter(id => currentlyAssociated.indexOf(id) < 0), (id) => {
                        return associate({related}, id);
                    });
                });
            });
    };

    this.saveRelatedSequentially = ({ related }, credentials) => {
        Rest.setUrl(related.credentials);
        return Rest
            .get()
            .then(res => {
                const { data: { results = [] } } = res;
                const updatedCredentialIds = (credentials || []).map(({ id }) => id);
                const currentCredentialIds = results.map(({ id }) => id);
                const credentialIdsToAssociate = [];
                const credentialIdsToDisassociate = [];
                let disassociateRemainingIds = false;

                currentCredentialIds.forEach((currentId, position) => {
                    if (!disassociateRemainingIds && updatedCredentialIds[position] !== currentId) {
                        disassociateRemainingIds = true;
                    }

                    if (disassociateRemainingIds) {
                        credentialIdsToDisassociate.push(currentId);
                    }
                });

                updatedCredentialIds.forEach(updatedId => {
                    if (credentialIdsToDisassociate.includes(updatedId)) {
                        credentialIdsToAssociate.push(updatedId);
                    } else if (!currentCredentialIds.includes(updatedId)) {
                        credentialIdsToAssociate.push(updatedId);
                    }
                });

                let disassociationPromise = Promise.resolve();
                credentialIdsToDisassociate.forEach(id => {
                    disassociationPromise = disassociationPromise.then(() => disassociate({ related }, id));
                });

                return disassociationPromise
                    .then(() => {
                        let associationPromise = Promise.resolve();
                        credentialIdsToAssociate.forEach(id => {
                            associationPromise = associationPromise.then(() => associate({ related }, id));
                        });
                        return associationPromise;
                    });
            });
    };

    this.getRelated = ({ related }, params = { permitted: [] }) => {
        Rest.setUrl(related.credentials);
        return Rest
            .get()
            .catch(handleError('GET', 'related credentials', params.permitted));
    };

    this.getCredentials = () => {
        Rest.setUrl(GetBasePath('credentials'));
        return Rest
            .get()
            .catch(handleError('GET', 'related credentials'));
    };

    this.getCredentialTypes = () => {
        Rest.setUrl(GetBasePath('credential_types'));
        return Rest
            .get({ params: { page_size: 200 }})
            .catch(handleError('GET', 'credential types'));
    };

    this.createTag = (credential, credential_types) => {
        const credentialTypeId = credential.credential_type || credential.credential_type_id;
        const credentialType = credential_types.find(t => t.id === credentialTypeId);

        return {
            id: credential.id,
            name: credential.name,
            kind: _.get(credentialType, 'kind'),
            typeName: _.get(credentialType, 'name'),
            info: _.get(credential, 'inputs.vault_id')
        };
    };
}

MultiCredentialService.$inject = [
    'Rest',
    'ProcessErrors',
    '$q',
    'GetBasePath',
];

export default MultiCredentialService;
