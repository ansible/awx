import actions from './sections/actions';
import breadcrumb from './sections/breadcrumb';
import createFormSection from './sections/createFormSection';
import createTableSection from './sections/createTableSection';
import header from './sections/header';
import search from './sections/search';
import pagination from './sections/pagination';

const addEditPanel = {
    selector: 'div[ui-view="form"]',
    elements: {
        title: 'div[class="Form-title"]',
    },
    sections: {
        details: createFormSection({
            selector: '#credential_type_form',
            labels: {
                name: 'Name',
                description: 'Description',
                inputConfiguration: 'Input Configuration',
                injectorConfiguration: 'Injector Configuration'
            },
            strategy: 'legacy'
        })
    }
};

const listPanel = {
    selector: 'div[ui-view="list"]',
    elements: {
        add: '#button-add',
        badge: 'div[class="List-titleBadge]',
        titleText: 'div[class="List-titleText"]',
        noitems: 'div[class="List-noItems"]'
    },
    sections: {
        search,
        pagination,
        table: createTableSection({
            elements: {
                name: 'td[class~="name-column"]',
                kind: 'td[class~="kind-column"]',
            },
            sections: {
                actions
            }
        })
    }
};

module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/credential_types`;
    },
    commands: [{
        load () {
            this.api.url('data:,'); // https://github.com/nightwatchjs/nightwatch/issues/1724
            return this.navigate();
        },
    }],
    sections: {
        header,
        breadcrumb,
        add: addEditPanel,
        edit: addEditPanel,
        list: listPanel
    }
};
