/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    function flatCompare(facts, nameKey, compareKeys) {

        var leftFacts = facts[0];
        var rightFacts = facts[1];

        return rightFacts.reduce(function(arr, rightFact) {
            var searcher = {};
            searcher[nameKey] = rightFact[nameKey];

            var isNewFactValue = false;

            var matchingFact = _.where(leftFacts, searcher);
            var diffs;

            if (_.isEmpty(matchingFact)) {
                isNewFactValue = true;

                diffs =
                    _.map(rightFact, function(value, key) {
                        return {   keyName: key,
                                    value1: value,
                                    value2: ''
                                };
                    });
            } else {
                matchingFact = matchingFact[0];

                diffs = _(compareKeys)
                    .map(function(key) {
                        var leftValue = rightFact[key];
                        var rightValue = matchingFact[key];
                        if (leftValue !== rightValue) {
                            return {
                                keyName: key,
                                value1: leftValue,
                                value2: rightValue
                            };
                        }
                    }).compact()
                    .value();

            }

            var descriptor =
                {   displayKeyPath: rightFact[nameKey],
                    isNew: isNewFactValue,
                    nestingLevel: 0,
                    facts: diffs
                };

            return arr.concat(descriptor);
        }, []).filter(function(diff) {
            return !_.isEmpty(diff.facts);
        });

    }
