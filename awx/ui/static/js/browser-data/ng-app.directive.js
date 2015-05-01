export default ['browserData', function(browserData) {
    return {
        link: function(scope, element, attrs) {
            element
                .attr('data-browser', browserData.userAgent)
                .attr('data-platform', browserData.platform);
        }
    };
}]
