export default [function() {
    return {
        /**
         * For the Smart Host Filter, values with spaces are wrapped with double quotes on input.
         * To avoid having these quoted values split up and treated as terms themselves, some
         * work is done to encode quotes in quoted values and the spaces within those quoted
         * values before calling to `splitSearchIntoTerms`.
         */
        splitFilterIntoTerms (searchString) {
            if (!searchString) {
                return null;
            }

            let groups = [];
            let quoted;

            // This split _may_ split search terms down the middle
            // ex) searchString=ansible_facts.some_other_thing:"foo foobar" ansible_facts.some_thing:"foobar"
            // would result in 3 different substring's but only two search terms
            // This logic handles that scenario with the `quoted` variable
            searchString.split(' ').forEach(substring => {
                if (/:"/g.test(substring)) {
                    if (/"$/.test(substring)) {
                        groups.push(this.encode(substring));
                    } else {
                        quoted = substring;
                    }
                } else if (quoted) {
                    quoted += ` ${substring}`;

                    if (/"/g.test(substring)) {
                        groups.push(this.encode(quoted));
                        quoted = undefined;
                    }
                } else {
                    groups.push(substring);
                }
            });

            return this.splitSearchIntoTerms(groups.join(' '));
        },
        encode (string) {
            string = string.replace(/'/g, '%27');

            return string.replace(/("| )/g, match => encodeURIComponent(match));
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
