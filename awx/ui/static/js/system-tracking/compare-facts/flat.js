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
    function flatCompare(basisFacts,
                         comparatorFacts, renderOptions) {

        var nameKey = renderOptions.nameKey;
        var compareKeys = renderOptions.compareKey;
        var keyNameMap = renderOptions.keyNameMap;
        var valueFormatter = renderOptions.valueFormatter;
        var factTemplate = renderOptions.factTemplate;


        return basisFacts.facts.reduce(function(arr, basisFact) {
            var searcher = {};
            searcher[nameKey] = basisFact[nameKey];

            var slottedValues, basisValue, comparatorValue;

            var matchingFact = _.where(comparatorFacts.facts, searcher);
            var diffs;

            // Perform comparison and get back comparisonResults; like:
            //  {   'value':
            //      {   leftValue: 'blah',
            //          rightValue: 'doo'
            //      }
            //  };
            //
            var comparisonResults =
                _.reduce(compareKeys, function(result, compareKey) {

                    if (_.isEmpty(matchingFact)) {
                        comparatorValue = 'absent';
                    } else {
                        comparatorValue = matchingFact[0][compareKey];
                    }

                    var slottedValues = slotFactValues(basisFacts.position,
                                                       basisFact[compareKey],
                                                       comparatorValue);

                    if (_.isUndefined(slottedValues.left) && _.isUndefined(slottedValues.right)) {
                        return result;
                    }

                    if (slottedValues.left !== slottedValues.right) {
                        slottedValues.isDivergent = true;
                    } else {
                        slottedValues.isDivergent = false;
                    }

                    result[compareKey] = slottedValues;

                    return result;
                }, {});

                var hasDiffs = _.any(comparisonResults, { isDivergent: true });

                if (hasDiffs && factTemplate.hasTemplate()) {

                    basisValue = factTemplate.render(basisFact);

                    if (_.isEmpty(matchingFact)) {
                        comparatorValue = 'absent';
                    } else {
                        comparatorValue = factTemplate.render(matchingFact[0]);
                    }

                    if (!_.isEmpty(comparisonResults)) {

                        slottedValues = slotFactValues(basisFact.position, basisValue, comparatorValue);

                        diffs =
                            {   keyName: basisFact[nameKey],
                                value1: slottedValues.left,
                                value2: slottedValues.right
                            };
                    }

                } else if (hasDiffs) {

                    diffs =
                        _(comparisonResults).map(function(slottedValues, key) {

                            var keyName = key;

                            if (keyNameMap && keyNameMap[key]) {
                                keyName = keyNameMap[key];
                            }

                            return {    keyName: keyName,
                                        value1: slottedValues.left,
                                        value1IsAbsent: slottedValues.left === 'absent',
                                        value2: slottedValues.right,
                                        value2IsAbsent: slottedValues.right === 'absent',
                                        isDivergent: slottedValues.isDivergent
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
