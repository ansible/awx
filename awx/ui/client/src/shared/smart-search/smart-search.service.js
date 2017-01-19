export default [function() {
    return {
        splitSearchIntoTerms(searchString) {
            return searchString.match(/(?:[^\s("')]+|"[^"]*"|'[^']*')+/g);
        },
        splitTermIntoParts(searchTerm) {
            let breakOnColon = searchTerm.match(/(?:[^:"]+|"[^"]*")+/g);

            if(breakOnColon.length > 2) {
                // concat all the strings after the first one together
                let stringsToJoin = breakOnColon.slice(1,breakOnColon.length);
                return [breakOnColon[0], stringsToJoin.join(':')];
            }
            else {
                return breakOnColon;
            }
        }
    };
}];
