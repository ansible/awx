function wrapper(rootScope) {
    return function compile(element, attrs) {
        var href, title, icon;
        if (rootScope.portalMode) {
            href = '#';
            title = 'Exit Portal Mode';
            icon = 'PortalMode--exit.svg';
        } else {
            href = '#portal';
            title = 'Portal Mode';
            icon = 'PortalMode.svg';
        }

        element
            .attr('href', href)
            .attr('title', title)
            .find('>img')
                .attr('src', '/static/img/' + icon);
    }
}

export default ['$rootScope', function($rootScope) {
    return {
        compile: wrapper($rootScope)
    };
}]
