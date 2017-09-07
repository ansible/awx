import search from './search.js';
import createTableSection from './createTableSection.js';


 module.exports = {
    selector: 'div[ui-view="related"]',
    sections: {
        list: {
            selector: '.List',
            elements: {
                add: 'button[class="btn List-buttonSubmit"]',
                badge: 'div[class="List-titleBadge]',
                titleText: 'div[class="List-titleText"]',
                noitems: 'div[class="List-noItems"]'
            },
            sections: {
                search,
                table: createTableSection({
                    selector: '#permissions_table',
                    rowElements: {
                        username: 'td[class~="username"]',
                        roles: 'td role-list:nth-of-type(1)',
                        teamRoles: 'td role-list:nth-of-type(2)'
                    }
                })
            }
        }
    }
};
