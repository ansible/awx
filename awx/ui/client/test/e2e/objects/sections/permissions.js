import actions from './actions.js';
import createTableSection from './createTableSection.js';
import pagination from './pagination.js';
import search from './search.js';


const permissions = {
    selector: 'div[ui-view="related"]',
    elements: {
        add: 'button[class="btn List-buttonSubmit"]',
        badge: 'div[class="List-titleBadge]',
        titleText: 'div[class="List-titleText"]',
        noitems: 'div[class="List-noItems"]'
    },
    sections: {
        search,
        pagination,
        table: createTableSection({
            elements: {
                username: 'td[class~="username"]',
                roles: 'td role-list:nth-of-type(1)',
                teamRoles: 'td role-list:nth-of-type(2)'
            },
            sections: { actions }
        })
    }
};


module.exports = permissions;
