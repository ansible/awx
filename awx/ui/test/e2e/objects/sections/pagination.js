const pagination = {
    selector: 'paginate div',
    elements: {
        first: 'i[class="fa fa-angle-double-left"]',
        previous: 'i[class="fa fa-angle-left"]',
        next: 'i[class="fa fa-angle-right"]',
        last: 'i[class="fa fa-angle-double-right"]',
        pageCount: 'span[class~="pageof"]',
        itemCount: 'span[class~="itemsOf"]',
    }
};

module.exports = pagination;
