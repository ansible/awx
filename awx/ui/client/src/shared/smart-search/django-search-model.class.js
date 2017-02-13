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
    constructor(name, baseFields, relatedSearchFields) {
        function trimRelated(relatedSearchField){
            return relatedSearchField.replace(/\__search$/, "");
        }
        this.name = name;
        this.related = _.map(relatedSearchFields, trimRelated);
        // Remove "object" type fields from this list
        for (var key in baseFields) {
            if (baseFields.hasOwnProperty(key)) {
                if (baseFields[key].type === 'object'){
                    delete baseFields[key];
                }
            }
        }
        delete baseFields.url;
        this.base = baseFields;
    }
}
