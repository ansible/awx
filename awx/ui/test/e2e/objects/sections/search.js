const search = {
    selector: 'smart-search',
    locateStrategy: 'css selector',
    elements: {
        clearAll: 'a[class*="clear"]',
        searchButton: 'i[class$="search"]',
        input: 'input',
        tags: '.SmartSearch-tagContainer'
    }
};

module.exports = search;
