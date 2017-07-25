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
        this.searchExamples = [];
        this.related = _.uniq(_.map(relatedSearchFields, trimRelated));
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
        if(baseFields.id) {
            this.searchExamples.push("id:>10");
        }
        // Loop across the base fields and try find one of type = string and one of type = datetime
        let stringFound = false,
            dateTimeFound = false;

        _.forEach(baseFields, (value, key) => {
            if(!stringFound && value.type === 'string') {
                this.searchExamples.push(key + ":foobar");
                stringFound = true;
            }
            if(!dateTimeFound && value.type === 'datetime') {
                this.searchExamples.push(key + ":>=2000-01-01T00:00:00Z");
                this.searchExamples.push(key + ":<2000-01-01");
                dateTimeFound = true;
            }
        });
    }
}
