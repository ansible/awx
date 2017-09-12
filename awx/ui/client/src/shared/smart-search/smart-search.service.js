export default [function() {
    return {
        /**
         * For the Smart Host Filter, values with spaces are wrapped with double quotes on input.
         * To avoid having these quoted values split up and treated as terms themselves, some
         * work is done to encode quotes in quoted values and the spaces within those quoted
         * values before calling to `splitSearchIntoTerms`.
         */
        splitHostIntoTerms (searchString) {
            let groups = [];
            let quoted;

            searchString.split(' ').forEach(substring => {
                if (substring.includes(':"')) {
                    quoted = substring;
                } else if (quoted) {
                    quoted += ` ${substring}`;

                    if (substring.includes('"')) {
                        quoted = quoted.replace(/"/g, encodeURIComponent('"'));
                        quoted = quoted.replace(/ /g, encodeURIComponent(' '));
                        groups.push(quoted);
                        quoted = undefined;
                    }
                } else {
                    groups.push(substring);
                }
            });

            return this.splitSearchIntoTerms(groups.join(' '));
        },
        splitSearchIntoTerms(searchString) {
            return searchString.match(/(?:[^\s"']+|"[^"]*"|'[^']*')+/g);
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
