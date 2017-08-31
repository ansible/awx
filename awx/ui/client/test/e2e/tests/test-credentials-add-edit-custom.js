import uuid from 'uuid';


let store = {
    credentialType: {
        name: `credentialType-${uuid().substr(0,8)}`,
        description: "custom cloud credential",
        kind: "cloud",
        inputs: {
            fields: [
                {
                    id: "project",
                    label: "Project",
                    type: "string",
                    help_text: "Name of your project"
                },
                {
                    id: "token",
                    label: "Token",
                    secret: true,
                    type: "string",
                    help_text: "help"
                },
                {
                    id: "secret_key_data",
                    label: "Secret Key",
                    type: "string",
                    secret: true,
                    multiline: true,
                    help_text: "help",
                },
                {
                    id: "public_key_data",
                    label: "Public Key",
                    type: "string",
                    secret: true,
                    multiline: true,
                    help_text: "help",
                },
                {
                    id: "secret_key_unlock",
                    label: "Private Key Passphrase",
                    type: "string",
                    secret: true,
                    //help_text: "help"
                },
                {
                    id: "color",
                    label: "Favorite Color",
                    choices: [
                        "",
                        "red",
                        "orange",
                        "yellow",
                        "green",
                        "blue",
                        "indigo",
                        "violet"
                    ],
                    help_text: "help",
                },
            ],
            required: ['project', 'token']
        },
        injectors: {
            env: {
                CUSTOM_CREDENTIAL_TOKEN: "{{ token }}"
            }
        }
    }
};


const inputs = store.credentialType.inputs;
const fields = store.credentialType.inputs.fields;
const help = fields.filter(f => f.help_text);
const required = fields.filter(f => inputs.required.indexOf(f.id) > -1);
const strings = fields.filter(f => f.type === undefined || f.type === 'string');


const getObjects = function(client) {
    let credentials = client.page.credentials();
    let details = credentials.section.add.section.details;
    let type = details.custom(store.credentialType);
    return { credentials, details, type };
};


module.exports = {
    before: function(client, done) {
        const credentials = client.page.credentials();

        client.login();
        client.waitForAngular();

        client.inject([store.credentialType, 'CredentialTypeModel'], (data, model) => {
            return new model().http.post(data);
        },
        ({ data }) => {
            store.credentialType.response = data;
        });

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
    'all fields are visible': function(client) {
        let { type } = getObjects(client);
        fields.map(f => type.expect.element(`@${f.id}`).visible);
    },
    'helplinks open popovers showing expected content': function(client) {
        let { type } = getObjects(client);

        help.map(f => {
            let group = type.section[f.id];
            group.expect.element('@popover').not.visible;
            group.click('@help');
            group.expect.element('@popover').visible;
            group.expect.element('@popover').text.to.contain(f.help_text);
            group.click('@help');
        });

        help.map(f => {
            let group = type.section[f.id];
            group.expect.element('@popover').not.visible;
        });
    },
    'secret field buttons hide and unhide input': function(client) {
        let { type } = getObjects(client);
        let secrets = strings.filter(f => f.secret && !f.multiline);

        secrets.map(f => {
            let group = type.section[f.id];
            let input = `@${f.id}`;

            group.expect.element('@show').visible;
            group.expect.element('@hide').not.present;

            type.setValue(input, 'SECRET');
            type.expect.element(input).text.equal('');

            group.click('@show');
            group.expect.element('@show').not.present;
            group.expect.element('@hide').visible;
            type.expect.element(input).value.contain('SECRET');

            group.click('@hide');
            group.expect.element('@show').visible;
            group.expect.element('@hide').not.present;
            type.expect.element(input).text.equal('');
        })
    },
    'required fields show * symbol': function(client) {
        let { type  } = getObjects(client);

        required.map(f => {
            let group = type.section[f.id];
            group.expect.element('@label').text.to.contain('*');
        });

        client.end();
    }
};
