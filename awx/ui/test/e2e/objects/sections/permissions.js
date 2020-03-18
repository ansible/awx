import actions from './actions';
import createTableSection from './createTableSection';
import pagination from './pagination';
import search from './search';

const permissions = {
    selector: 'div[ui-view="related"]',
    elements: {
        add: '#button-add--permission',
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
