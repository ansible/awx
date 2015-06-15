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
        var factTemplate = renderOptions.factTemplate;


        return basisFacts.facts.reduce(function(arr, basisFact) {
            var searcher = {};
            searcher[nameKey] = basisFact[nameKey];

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

                    var comparatorFact = matchingFact[0] || {};
                    var isNestedDisplay = false;

                    var slottedValues = slotFactValues(basisFacts.position,
                                                       basisFact[compareKey],
                                                       comparatorFact[compareKey]);

                    if (_.isUndefined(slottedValues.left) && _.isUndefined(slottedValues.right)) {
                        return result;
                    }

                    var template = factTemplate;

                    if (_.isObject(template) && template.hasOwnProperty(compareKey)) {
                        template = template[compareKey];

                        // 'true' means render the key without formatting
                        if (template === true) {
                            template =
                                {   render: function(fact) { return fact[compareKey]; }
                                };
                        }

                        isNestedDisplay = true;
                    } else if (typeof template.hasTemplate === 'function' && !template.hasTemplate()) {
                        template =
                            {   render: function(fact) { return fact[compareKey]; }
                            };
                        isNestedDisplay = true;
                    } else if (typeof factTemplate.render === 'function') {
                        template = factTemplate;
                    } else if (!template.hasOwnProperty(compareKey)) {
                        return result;
                    }

                    if (basisFacts.position === 'left') {
                        slottedValues.left = template.render(basisFact);
                        slottedValues.right = template.render(comparatorFact);
                    } else {
                        slottedValues.left = template.render(comparatorFact);
                        slottedValues.right = template.render(basisFact);
                    }

                    if (slottedValues.left !== slottedValues.right) {
                        slottedValues.isDivergent = true;
                    } else {
                        slottedValues.isDivergent = false;
                    }

                    if (isNestedDisplay) {
                        result[compareKey] = slottedValues;
                    } else {
                        result = slottedValues;
                    }

                    return result;
                }, {});

                var hasDiffs =
                    _.any(comparisonResults, { isDivergent: true }) ||
                        comparisonResults.isDivergent === true;

                if (hasDiffs && typeof factTemplate.render === 'function') {

                    diffs =
                        {  keyName: basisFact[nameKey],
                            value1: comparisonResults.left,
                            value2: comparisonResults.right
                        };

                } else if (hasDiffs) {

                    diffs =
                        _(comparisonResults).map(function(slottedValues, key) {

                            var keyName = key;

                            if (keyNameMap && keyNameMap[key]) {
                                keyName = keyNameMap[key];
                            }

                            return {    keyName: keyName,
                                        value1: slottedValues.left,
                                        value2: slottedValues.right,
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
