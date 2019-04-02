import uuid from 'uuid';

const store = {
    credentialType: {
        name: `credentialType-${uuid().substr(0, 8)}`,
        description: 'custom cloud credential',
        kind: 'cloud',
        inputs: {
            fields: [
                {
                    id: 'project',
                    label: 'Project',
                    type: 'string',
                    help_text: 'Name of your project'
                },
                {
                    id: 'token',
                    label: 'Token',
                    secret: true,
                    type: 'string',
                    help_text: 'help'
                },
                {
                    id: 'secret_key_data',
                    label: 'Secret Key',
                    type: 'string',
                    secret: true,
                    multiline: true,
                    help_text: 'help',
                },
                {
                    id: 'public_key_data',
                    label: 'Public Key',
                    type: 'string',
                    secret: true,
                    multiline: true,
                    help_text: 'help',
                },
                {
                    id: 'secret_key_unlock',
                    label: 'Private Key Passphrase',
                    type: 'string',
                    secret: true,
                    // help_text: 'help'
                },
                {
                    id: 'color',
                    label: 'Favorite Color',
                    choices: [
                        '',
                        'red',
                        'orange',
                        'yellow',
                        'green',
                        'blue',
                        'indigo',
                        'violet'
                    ],
                    help_text: 'help',
                },
            ],
            required: ['project', 'token']
        },
        injectors: {
            env: {
                CUSTOM_CREDENTIAL_TOKEN: '{{ token }}'
            }
        }
    }
};

const { inputs } = store.credentialType;
const { fields } = inputs;
const help = fields.filter(f => f.help_text);
const required = fields.filter(f => inputs.required.indexOf(f.id) > -1);
const strings = fields.filter(f => f.type === undefined || f.type === 'string');

const getObjects = client => {
    const credentials = client.page.credentials();
    const { details } = credentials.section.add.section;
    const type = details.custom(store.credentialType);

    return { credentials, details, type };
};

module.exports = {
    before: (client, done) => {
        const credentials = client.page.credentials();

        client.login();
        client.waitForAngular();

        client.inject(
            [store.credentialType, 'CredentialTypeModel'],
            (data, Model) => new Model().http.post({ data }),
            ({ data }) => { store.credentialType.response = data; }
        );

        credentials.section.navigation
            .waitForElementVisible('@credentials')
            .click('@credentials');

        credentials
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny');

        credentials.section.list
            .waitForElementVisible('@add')
            .click('@add');

        credentials.section.add.section.details
            .waitForElementVisible('@save')
            .setValue('@name', `cred-${uuid()}`)
            .setValue('@type', store.credentialType.name, done);
    },
    'all fields are visible': client => {
        const { type } = getObjects(client);
        fields.forEach(f => {
            type.expect.element(`@${f.id}`).visible;
        });
    },
    'helplinks open popovers showing expected content': client => {
        const { type } = getObjects(client);

        help.forEach(f => {
            const group = type.section[f.id];

            group.expect.element('@popover').not.visible;
            group.click('@help');
            group.expect.element('@popover').visible;
            group.expect.element('@popover').text.to.contain(f.help_text);
            group.click('@help');
        });

        help.forEach(f => {
            const group = type.section[f.id];
            group.expect.element('@popover').not.visible;
        });
    },
    'secret field buttons hide and unhide input': client => {
        const { type } = getObjects(client);
        const secrets = strings.filter(f => f.secret && !f.multiline);

        secrets.forEach(f => {
            const group = type.section[f.id];
            const input = `@${f.id}`;

            group.expect.element('@show').visible;
            group.expect.element('@hide').not.visible;

            type.setValue(input, 'SECRET');
            type.expect.element(input).text.equal('');

            group.click('@show');
            group.expect.element('@show').not.visible;
            group.expect.element('@hide').visible;
            type.expect.element(input).value.contain('SECRET');

            group.click('@hide');
            group.expect.element('@show').visible;
            group.expect.element('@hide').not.visible;
            type.expect.element(input).text.equal('');
        });
    },
    'required fields show * symbol': client => {
        const { type } = getObjects(client);

        required.forEach(f => {
            const group = type.section[f.id];
            group.expect.element('@label').text.to.contain('*');
        });

        client.end();
    }
};
