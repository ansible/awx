// Ignored fields are not surfaced in the UI's search key
let isIgnored = function(key, value) {
    let ignored = [
        'type',
        'url',
        'related',
        'summary_fields',
        'object_roles',
        'activity_stream',
        'update',
        'teams',
        'users',
        'owner_teams',
        'owner_users',
        'access_list',
        'notification_templates_error',
        'notification_templates_success',
        'ad_hoc_command_events',
        'fact_versions',
        'variable_data',
        'playbooks'
    ];
    return ignored.indexOf(key) > -1 || value.type === 'field';
};

export default
class DjangoSearchModel {
    /*
        @property name - supplied model name
        @property base {
            field: {
                type: 'string' // string, bool, field, choice, datetime,
                label: 'Label', // Capitalized
                help_text: 'Some helpful descriptive text'
            }
        }
        @@property related ['field' ...]
    */
    constructor(name, endpoint, baseFields, relations) {
        let base = {};
        this.name = name;
        this.related = _.reject(relations, isIgnored);
        _.forEach(baseFields, (value, key) => {
            if (!isIgnored(key, value)) {
                base[key] = value;
            }
        });
        this.base = base;
    }

    fields() {
        let result = this.base;
        result.related = this.related;
        return result;
    }
}
