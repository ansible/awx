const search = {
    selector: 'smart-search',
    locateStrategy: 'css selector',
    elements: {
        clearAll: 'a[class*="clearAll"]',
        searchButton: 'i[class*="fa-search"]',
        input: 'input',
        tags: '.SmartSearch-tagContainer'
    }
};

module.exports = search;
