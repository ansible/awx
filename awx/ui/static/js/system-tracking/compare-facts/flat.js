/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    function flatCompare(facts, nameKey, compareKeys) {

        var comparatorFacts = facts[0];
        var basisFacts = facts[1];

        return basisFacts.reduce(function(arr, basisFact) {
            var searcher = {};
            searcher[nameKey] = basisFact[nameKey];

            var isNewFactValue = false;

            var matchingFact = _.where(comparatorFacts, searcher);
            var diffs;

            if (_.isEmpty(matchingFact)) {
                isNewFactValue = true;

                diffs =
                    _.map(basisFact, function(value, key) {
                        return {   keyName: key,
                                    value1: value,
                                    value2: ''
                                };
                    });
            } else {
                matchingFact = matchingFact[0];

                diffs = _(compareKeys)
                    .map(function(key) {
                        var basisValue = basisFact[key];
                        var comparatorValue = matchingFact[key];
                        var leftValue, rightValue;

                        if (basisFacts.position === 'left') {
                            leftValue = basisValue;
                            rightValue = comparatorValue;
                        } else {
                            rightValue = basisValue;
                            leftValue = comparatorValue;
                        }

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
                {   displayKeyPath: basisFact[nameKey],
                    isNew: isNewFactValue,
                    nestingLevel: 0,
                    facts: diffs
                };

            return arr.concat(descriptor);
        }, []).filter(function(diff) {
            return !_.isEmpty(diff.facts);
        });

    }
