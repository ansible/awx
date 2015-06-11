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

            if (_.isEmpty(matchingFact)) {

                if (!_.isUndefined(factTemplate)) {

                    basisValue = factTemplate.render(basisFact);
                    slottedValues = slotFactValues(basisFacts.position, basisValue, 'absent');

                    diffs =
                        {   keyName: basisFact[nameKey],
                            value1: slottedValues.left,
                            value2: slottedValues.right
                        };

                } else {

                    diffs =
                        _.map(basisFact, function(value, key) {
                            var slottedValues = slotFactValues(basisFacts.position, value, 'absent');

                            return {    keyName: key,
                                        value1: slottedValues.left,
                                        value1IsAbsent: slottedValues.left === 'absent',
                                        value2: slottedValues.right,
                                        value2IsAbsent: slottedValues.right === 'absent'
                                   };
                        });
                }
            } else {

                matchingFact = matchingFact[0];

                if (!_.isUndefined(factTemplate)) {

                    basisValue = factTemplate.render(basisFact);
                    comparatorValue = factTemplate.render(matchingFact);

                    slottedValues = slotFactValues(basisFacts.position, basisValue, comparatorValue);

                    if (basisValue !== comparatorValue) {

                        diffs =
                            {   keyName: basisFact[nameKey],
                                value1: slottedValues.left,
                                value2: slottedValues.right
                            };

                    }

                } else {

                    diffs = _(compareKeys)
                        .map(function(key) {
                            var slottedValues = slotFactValues(basisFacts.position,
                                                               basisFact[key],
                                                               matchingFact[key]);

                            if (slottedValues.left !== slottedValues.right) {
                                return {
                                    keyName: basisFact[nameKey],
                                    value1: slottedValues.left,
                                    value2: slottedValues.right
                                };
                            }
                        }).compact()
                        .value();
                }

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
