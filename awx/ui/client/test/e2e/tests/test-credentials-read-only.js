import uuid from 'uuid';


let testID = uuid().substr(0,8);


let store = {
    auditor: {
        username: `auditor-${testID}`,
        first_name: 'auditor',
        last_name: 'last',
        email: 'null@ansible.com',
        is_superuser: false,
        is_system_auditor: true,
        password: 'password'
    },
    adminCredential: {
        name: `adminCredential-${testID}`,
        description: `adminCredential-description-${testID}`,
        inputs: {
            username: 'username',
            password: 'password',
            security_token: 'AAAAAAAAAAAAAAAAAAAAAAAAAA'
        }
    },
    created: {}
};


module.exports = {
    before: function (client, done) {
        const credentials = client.page.credentials();

        client.login();
        client.waitForAngular();

        client.inject([store, '$http'], (store, $http) => {

            let { adminCredential, auditor } = store;

            return $http.get('/api/v2/me')
                .then(({ data }) => {
                    let resource = 'Amazon%20Web%20Services+cloud';
                    adminCredential.user = data.results[0].id;

                    return $http.get(`/api/v2/credential_types/${resource}`);
                })
                .then(({ data }) => {
                    adminCredential.credential_type = data.id;

                    return $http.post('/api/v2/credentials/', adminCredential);
                })
                .then(({ data }) => {
                    adminCredential = data;

                    return $http.post('/api/v2/users/', auditor);
                })
                .then(({ data }) => {
                    auditor = data;

                    return { adminCredential, auditor };
                });
        },
        ({ adminCredential, auditor }) => {
            store.created = { adminCredential, auditor };
            done();
        })
    },
    beforeEach: function (client) {
        const credentials = client.useCss().page.credentials();

        credentials
            .login(store.auditor.username, store.auditor.password)
            .navigate(`${credentials.url()}/${store.created.adminCredential.id}/`)
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny');
    },
    'verify an auditor\'s inputs are read-only': function (client) {
        const credentials = client.useCss().page.credentials()
        const details = credentials.section.edit.section.details;

        let expected = store.created.adminCredential.name;

        credentials.section.edit
            .expect.element('@title').text.contain(expected);

        client.elements('css selector', '.at-Input', inputs => {
            inputs.value.map(o => o.ELEMENT).forEach(id => {
                client.elementIdAttribute(id, 'disabled', ({ value }) => {
                    client.assert.equal(value, 'true');
                });
            });
        });

        client.end();
    }
};
