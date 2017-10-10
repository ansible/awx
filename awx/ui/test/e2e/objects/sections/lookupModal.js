import createTableSection from './createTableSection.js';
import pagination from './pagination.js';
import search from './search.js';


const lookupModal = {
    selector: '#form-modal',
    elements: {
        close: 'i[class="fa fa-times-circle"]',
        title: 'div[class^="Form-title"]',
        select: 'button[class*="save"]',
        cancel: 'button[class*="cancel"]'
    },
    sections: {
        search,
        pagination,
        table: createTableSection({
            elements: {
                name: 'td[class~="name-column"]',
                selected: 'input[type="radio", value="1"]',
            }

        })
    }
};

module.exports = lookupModal;
