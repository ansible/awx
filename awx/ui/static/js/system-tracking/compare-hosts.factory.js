export default
    ['xorObjects', 'formatResults', function(xorObjects, formatResults) {
        return function compareHosts(module, factData1, factData2) {
            var diffed = xorObjects('name', factData1, factData2);
            return formatResults('name', 'version', diffed);
        };
    }];
