import createTableSection from './createTableSection';
import pagination from './pagination';
import search from './search';

const lookupModal = {
    selector: '#form-modal',
    elements: {
        close: 'i[class="fa fa-times-circle"]',
        title: 'div[class^="Form-title"]',
        select: 'button[class*="save"]',
        cancel: 'button[class*="cancel"]',
        save: 'button[class*="save"]'
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
