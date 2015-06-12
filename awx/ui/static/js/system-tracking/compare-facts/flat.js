/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function slotFactValues(basisPosition, basisValue, comparatorValue) {
    var leftValue, rightValue;

    if (basisPosition === 'left') {
        leftValue = basisValue;
        rightValue = comparatorValue;
    } else {
        rightValue = basisValue;
        leftValue = comparatorValue;
    }

    return  {    left: leftValue,
                 right: rightValue
            };
}

export default
    function flatCompare(basisFacts, comparatorFacts, nameKey, compareKeys, factTemplate) {


        return basisFacts.facts.reduce(function(arr, basisFact) {
            var searcher = {};
            searcher[nameKey] = basisFact[nameKey];

            var slottedValues, basisValue, comparatorValue;

            var matchingFact = _.where(comparatorFacts.facts, searcher);
            var diffs;

                if (!_.isUndefined(factTemplate)) {

                    basisValue = factTemplate.render(basisFact);

                    if (_.isEmpty(matchingFact)) {
                        comparatorValue = 'absent';
                    } else {
                        comparatorValue = factTemplate.render(matchingFact[0]);
                    }

                    slottedValues = slotFactValues(basisFacts.position, basisValue, comparatorValue);

                    diffs =
                        {   keyName: basisFact[nameKey],
                            value1: slottedValues.left,
                            value2: slottedValues.right
                        };

                } else {

                    if (_.isEmpty(matchingFact)) {
                        matchingFact = {};
                    } else {
                        matchingFact = matchingFact[0];
                    }

                    diffs =
                        _(basisFact).map(function(value, key) {
                            var slottedValues = slotFactValues(basisFacts.position, value, matchingFact[key] || 'absent');
                            var keyName;

                            if (slottedValues.right !== 'absent') {
                                if(slottedValues.left === slottedValues.right) {
                                    return;
                                }

                                if (!_.include(compareKeys, key)) {
                                    return;
                                }
                                 keyName = basisFact[nameKey];
                            } else {
                                keyName = key;
                            }

                            return {    keyName: keyName,
                                        value1: slottedValues.left,
                                        value1IsAbsent: slottedValues.left === 'absent',
                                        value2: slottedValues.right,
                                        value2IsAbsent: slottedValues.right === 'absent'
                                   };
                        }).compact()
                        .value();
                }

            var descriptor =
                    {   displayKeyPath: basisFact[nameKey],
                        nestingLevel: 0,
                        facts: diffs
                    };

            return arr.concat(descriptor);
        }, []).filter(function(diff) {
            return !_.isEmpty(diff.facts);
        });

    }
