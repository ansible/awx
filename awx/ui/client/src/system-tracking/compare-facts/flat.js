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

/*
 * @name flatCompare
 * @description
 *  Takes two separate fact objects and combines any differences into a single result
 *  object, formatted for display.
 *
 * @param {Tower.SystemTracking.ResolvedFact} basisFacts - The facts we will use as the basis for this comparison
 * @param {Tower.SystemTracking.ResolvedFact} comparatorFacts - The facts we will compare against the basis
 * @param {Tower.SystemTracking.RenderOptions} renderOptions - Options specified in the module for rendering values
 *
 * @returns {Array.<Tower.SystemTracking.FactComparisonDescriptor>}
 *
 * @typedef {Object} Tower.SystemTracking.RenderOptions
 * @property {string} nameKey - The name of the key that is used to locate facts from basisFacts in comparatorFacts
 * @property {string|string[]} compareKey - A single key or list of keys to compare in the two fact collections
 * @property {Tower.SystemTracking.KeyNameMap} keyNameMap - An object mapping existing key names to new key names for display
 * @property {Tower.SystemTracking.FactTemplate} factTemplate - An optional template used as the string for comparing and displaying a fact
 * @property {boolean} supportsValueArray - Indicates that the module we're rendering supports values in an array of strings rather than just a string; iterim measure to make sure modules with multiple facts matching nameKey don't get evaluated because we won't know how to dipslay them
 *
 * @typedef {(string|boolean)} Tower.SystemTracking.KeyNameMapValue - The name you want to use for the display of a key or "true" to indicate a key should be displayed without changing its name (all keys are hidden by default)
 *
 * @typedef {Object.<string, Tower.SystemTracking.KeyNameMapValue>} Tower.SystemTracking.KeyNameMap - An object whose keys are the names of keys that exist in a fact and whose values control how that key is displayed
 *
 * @typedef {{displayKeyPath: string, nestingLevel: number, facts: Array.<Tower.SystemTracking.FactComparisonResult>}} Tower.SystemTracking.FactComparisonDescriptor
 *
 * @typedef {{keyName: string, value1: Tower.SystemTracking.FactComparisonValue, value2: Tower.SystemTracking.FactComparisonValue, isDivergent: boolean}} Tower.SystemTracking.FactComparisonResult
 *
 * @typedef {(string|string[])} Tower.SystemTracking.FactComparisonValue
 *
 */
export default
    function flatCompare(basisFacts,
                         comparatorFacts, renderOptions) {

        var nameKey = renderOptions.nameKey;
        var compareKeys = renderOptions.compareKey;
        var keyNameMap = renderOptions.keyNameMap;
        var factTemplate = renderOptions.factTemplate;


        return basisFacts.facts.reduce(function(arr, basisFact) {

            // First, make sure this fact hasn't already been processed, if it
            // has don't process it again
            //
            if (_.any(arr, { displayKeyPath: basisFact[nameKey] })) {
                return arr;
            }

            var searcher = {};
            searcher[nameKey] = basisFact[nameKey];

            var containsValueArray = false;
            var matchingFacts = _.where(comparatorFacts.facts, searcher);
            var comparisonResults;
            var diffs;

            // If this fact exists more than once in `basisFacts`, then
            // we need to process it differently
            //
            var otherBasisFacts = _.where(basisFacts.facts, searcher);
            if (renderOptions.supportsValueArray && otherBasisFacts.length > 1) {
                comparisonResults = processFactsForValueArray(basisFacts.position, otherBasisFacts, matchingFacts);
            } else {
                comparisonResults = processFactsForSingleValue(basisFact, matchingFacts[0] || {});
            }

            function processFactsForValueArray(basisPosition, basisFacts, comparatorFacts) {

                function renderFactValues(facts) {
                    return facts.map(function(fact) {
                        return factTemplate.render(fact);
                    });
                }

                var basisFactValues = renderFactValues(basisFacts);
                var comparatorFactValues = renderFactValues(comparatorFacts);

                var slottedValues = slotFactValues(basisPosition, basisFactValues, comparatorFactValues);

                var remaining = _.difference(slottedValues.left, slottedValues.right);

                if (_.isEmpty(remaining)) {
                    slottedValues.isDivergent = false;
                } else {
                    slottedValues.isDivergent = true;
                    containsValueArray = true;
                }

                return slottedValues;
            }

            function processFactsForSingleValue(basisFact, comparatorFact) {
                // Perform comparison and get back comparisonResults; like:
                //  {   'value':
                //      {   leftValue: 'blah',
                //          rightValue: 'doo'
                //      }
                //  };
                //
                return _.reduce(compareKeys, function(result, compareKey) {

                        var isNestedDisplay = false;
                        var basisFactValue = basisFact[compareKey];
                        var comparatorFactValue = comparatorFact[compareKey];
                        var slottedValues;

                        if (_.isUndefined(basisFactValue) && _.isUndefined(comparatorFactValue)) {
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

                        // if (!renderOptions.supportsValueArray) {
                        //     comparatorFact = comparatorFact[0];
                        // }

                        basisFactValue = template.render(basisFact);
                        comparatorFactValue = template.render(comparatorFact);

                        slottedValues = slotFactValues(basisFacts.position,
                                                       basisFactValue,
                                                       comparatorFactValue);

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
            }

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
                        containsValueArray: containsValueArray,
                        facts: diffs
                    };

            return arr.concat(descriptor);
        }, []).filter(function(diff) {
            return !_.isEmpty(diff.facts);
        });

    }
