export default ['Rest', 'ProcessErrors', '$q', 'GetBasePath', function(Rest, ProcessErrors, $q, GetBasePath) {
    let val = {};

    // given an array of creds, POST them to url and return an array
    // of promises
    val.saveExtraCredentials = ({creds, url, disassociate = false,
        msg = "Failed to add extra credential.  POST returned status:"}) => {
            if (creds && creds[0] && typeof creds[0] !== 'number') {
                creds = creds.map(cred => cred.id);
            }

            return creds.map((cred_id) => {
                let payload = {'id': cred_id};

                if (disassociate) {
                  payload.disassociate = true;
                }

                Rest.setUrl(url);

                return Rest.post(payload)
                    .catch(({data, status}) => {
                        ProcessErrors(
                            null, data, status, null,
                            {
                                hdr: 'Error!',
                                msg: `${msg} ${status}`
                            });
                    });
            });
    };

    // removes credentials no longer a part of the jt, and adds
    // new ones
    val.findChangedExtraCredentials = ({creds, url}) => {
        Rest.setUrl(url);
        Rest.get()
            .then(({data}) => {
                let existingCreds = data.results
                    .map(cred => cred.id);

                let newCreds = creds
                    .map(cred => cred.id);

                let [toAdd, toRemove] = _.partition(_.xor(existingCreds,
                    newCreds), cred => (newCreds.indexOf(cred) > -1));

                let destroyResolve = [];

                destroyResolve = val.saveExtraCredentials({
                    creds: toRemove,
                    url: url,
                    disassociate: true,
                    msg: `Failed to disassociate existing credential.
                        POST returned status:`
                });

                $q.all(destroyResolve).then(() => {
                    val.saveExtraCredentials({
                        creds: toAdd,
                        url: url
                    });
                });


            })
            .catch(({data, status}) => {
                ProcessErrors(null, data, status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to get existing extra credentials. GET ' +
                        'returned status: ' + status
                });
            });
    };

    // calls credential types and returns the data needed to set up the
    // credential type selector
    val.getCredentialTypes = () => {
        Rest.setUrl(GetBasePath('credential_types'));
        return Rest.get()
            .then(({data}) => {
                let credential_types = {}, credentialTypeOptions = [];

                data.results.forEach((credentialType => {
                    credential_types[credentialType.id] = credentialType;
                    if(credentialType.kind
                        .match(/^(machine|cloud|net|ssh|vault)$/)) {
                            credentialTypeOptions.push({
                                name: credentialType.name,
                                value: credentialType.id
                            });
                    }
                }));

                return {
                    credential_types,
                    credentialTypeOptions
                };
            })
            .catch(({data, status}) => {
                ProcessErrors(null, data, status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to get credential types. GET returned ' +
                        'status: ' + status
                });
            });
    };

    // converts structured selected credential data into array for tag-based
    // view
    val.updateCredentialTags = (creds, typeOpts) => {
        let machineCred = [];
        let extraCreds = [];
        let vaultCred = [];

        if (creds.machine) {
            let mach = creds.machine;
            mach.postType = "machine";
            machineCred = [mach];
        }

        if (creds.vault) {
            let vault = creds.vault;
            vault.postType = "vault";
            vaultCred = [vault];
        }

        if (creds.extra) {
            extraCreds = creds.extra
                .map((cred) => {
                    cred.postType = "extra";

                    return cred;
                });
        }

        return machineCred.concat(extraCreds).concat(vaultCred).map(cred => ({
            name: cred.name,
            id: cred.id,
            postType: cred.postType,
            readOnly: cred.readOnly ? true : false,
            kind: typeOpts
                .filter(type => {
                    return parseInt(cred.credential_type) === type.value;
                })[0].name + ":"
        }));
    };

    // remove credential from structured selected credential data and tag-view
    // array
    val.removeCredential = (credToRemove, structuredObj, tagArr) => {
        tagArr.forEach((cred) => {
            if (credToRemove === cred.id) {
                if (cred.postType === 'machine') {
                    structuredObj[cred.postType] = null;
                } else if (cred.postType === 'vault') {
                    structuredObj[cred.postType] = null;
                } else {
                    structuredObj[cred.postType] = structuredObj[cred.postType]
                        .filter(cred => cred
                            .id !== credToRemove);
                }
            }
        });

        tagArr = tagArr
            .filter(cred => cred.id !== credToRemove);

        return [structuredObj, tagArr];
    };

    // load all relevant credential data to populate job template edit form
    val.loadCredentials = (data) => {
        let selectedCredentials = {
            machine: null,
            vault: null,
            extra: []
        }, credTypes, credTypeOptions, credTags;

        let credDefers = [];
        let job_template_obj = data;
        let credentialGetPermissionDenied = false;

        // get machine credential
        if (data.related.credential) {
            Rest.setUrl(data.related.credential);
            credDefers.push(Rest.get()
                .then(({data}) => {
                    selectedCredentials.machine = data;
                })
                .catch(({data, status}) => {
                    if (status === 403) {
                        /* User doesn't have read access to the machine credential, so use summary_fields */
                        credentialGetPermissionDenied = true;
                        selectedCredentials.machine = job_template_obj.summary_fields.credential;
                        selectedCredentials.machine.credential_type = job_template_obj.summary_fields.credential.credential_type_id;
                        selectedCredentials.machine.readOnly = true;
                    } else {
                        ProcessErrors(
                            null, data, status, null,
                            {
                                hdr: 'Error!',
                                msg: 'Failed to get machine credential. ' +
                                'Get returned status: ' +
                                status
                        });
                    }
                }));
        }

        if (data.related.vault_credential) {
            Rest.setUrl(data.related.vault_credential);
            credDefers.push(Rest.get()
                .then(({data}) => {
                    selectedCredentials.vault = data;
                })
                .catch(({data, status}) => {
                    if (status === 403) {
                        /* User doesn't have read access to the vault credential, so use summary_fields */
                        credentialGetPermissionDenied = true;
                        selectedCredentials.vault = job_template_obj.summary_fields.vault_credential;
                        selectedCredentials.vault.credential_type = job_template_obj.summary_fields.vault_credential.credential_type_id;
                        selectedCredentials.vault.readOnly = true;
                    } else {
                        ProcessErrors(
                            null, data, status, null,
                            {
                                hdr: 'Error!',
                                msg: 'Failed to get machine credential. ' +
                                'Get returned status: ' +
                                status
                        });
                    }
                }));
        }

        // get extra credentials
        if (data.related.extra_credentials) {
            Rest.setUrl(data.related.extra_credentials);
            credDefers.push(Rest.get()
                .then(({data}) => {
                    selectedCredentials.extra = data.results;
                })
                .catch(({data, status}) => {
                    if (status === 403) {
                        /* User doesn't have read access to the extra credentials, so use summary_fields */
                        credentialGetPermissionDenied = true;
                        selectedCredentials.extra = job_template_obj.summary_fields.extra_credentials;
                        _.map(selectedCredentials.extra, (cred) => {
                            cred.credential_type = cred.credential_type_id;
                            cred.readOnly = true;
                            return cred;
                        });
                    } else {
                        ProcessErrors(null, data, status, null,
                            {
                                hdr: 'Error!',
                                msg: 'Failed to get extra credentials. ' +
                                'Get returned status: ' +
                                status
                            });
                    }
                }));
        }

        // get credential types
        credDefers.push(val.getCredentialTypes()
            .then(({credential_types, credentialTypeOptions}) => {
                credTypes = credential_types;
                credTypeOptions = credentialTypeOptions;
            }));

        return $q.all(credDefers).then(() => {
            // get credential tags
            credTags = val
                .updateCredentialTags(selectedCredentials, credTypeOptions);

            return [selectedCredentials, credTypes, credTypeOptions,
                credTags, credentialGetPermissionDenied];
        });
    };

    return val;
}];
