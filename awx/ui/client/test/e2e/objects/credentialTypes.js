import breadcrumb from './sections/breadcrumb.js';
import createFormSection from './sections/createFormSection.js';
import createTableSection from './sections/createTableSection.js';
import header from './sections/header.js';
import search from './sections/search.js';


const addEditPanel = {
    selector: 'div[ui-view="form"]',
    elements: {
        title: '.List-title', 
    },
    sections: {
        details: createFormSection({
            selector: '#credential_type_form',
            labels: {
                name: "Name",
                description: "Description",
                inputConfiguration: "Input Configuration",
                injectorConfiguration: "Injector Configuration"
            },
            strategy: 'legacy'
        })
    }
};


const listPanel = {
    selector: 'div[ui-view="list"]',
    elements: {
        add: '.List-buttonSubmit',
        badge: 'div[class="List-titleBadge]',
        titleText: 'div[class="List-titleText"]',
        noitems: 'div[class="List-noItems"]'
    },
    sections: {
        search,
        table: createTableSection({
            selector: '#credential_types_table',
            rowElements: {
                name: 'td[class~="name-column"]',
                kind: 'td[class~="kind-column"]',
                edit: 'i[class="fa fa-pencil"]',
                delete: 'i[class="fa fa-trash-o"]'
            },
        })
    }
};


module.exports = {
    url() {
        return `${this.api.globals.awxURL}/#/credential_types`
    },
    sections: {
        header,
        breadcrumb,
        add: addEditPanel,
        edit: addEditPanel,
        list: listPanel
    }
};
