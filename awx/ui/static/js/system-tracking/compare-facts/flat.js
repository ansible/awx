/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    function flatCompare(facts, nameKey, compareKeys) {

        // Make sure we always start comparison against
        // a non-empty array
        //
        // Partition with _.isEmpty will give me an array
        // with empty arrays in index 0, and non-empty
        // arrays in index 1
        //

        // Save the position of the data so we
        // don't lose it later

        facts[0].position = 'left';
        facts[1].position = 'right';

        var splitFacts = _.partition(facts, _.isEmpty);
        var emptyScans = splitFacts[0];
        var nonEmptyScans = splitFacts[1];
        var basisFacts, comparatorFacts;

        if (_.isEmpty(nonEmptyScans)) {
            // we have NO data, so don't bother!
            return [];
        } else if (_.isEmpty(emptyScans)) {
            // both scans have facts, rejoice!
            comparatorFacts = nonEmptyScans[0];
            basisFacts = nonEmptyScans[1];
        } else {
            // only one scan has facts, so we use that
            // as the basis for our comparison
            basisFacts = nonEmptyScans[0];
            comparatorFacts = [];
        }

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
