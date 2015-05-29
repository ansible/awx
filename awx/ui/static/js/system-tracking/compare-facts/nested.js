/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {formatFacts, findFacts} from './nested-helpers';

export default function nestedCompare(factsList) {

    factsList = findFacts(factsList);
    factsList = compareFacts(factsList);
    return formatFacts(factsList);

    function compareFacts(factsList) {

        function serializedFactKey(fact) {
            return fact.keyPath.join('.');
        }

        var groupedByParent =
            _.groupBy(factsList, function(fact) {
                return serializedFactKey(fact);
            });


        var diffed = _.mapValues(groupedByParent, function(facts) {
            return facts.filter(function(fact) {
                return fact.value1 !== fact.value2;
            }).map(function(fact) {
                // TODO: Can we determine a "compare order" and be able say
                // which property is actually divergent?
                return _.merge({}, fact, { isDivergent: true });
            });
        });

        var itemsWithDiffs =
            _.filter(factsList, function(facts) {
                var groupedData = diffed[serializedFactKey(facts)];
                return !_.isEmpty(groupedData);
            });

        var keysWithDiffs =
            _.reduce(diffed, function(diffs, facts, key) {
                diffs[key] =
                    facts.reduce(function(diffKeys, fact) {
                        if (fact.isDivergent) {
                            return diffKeys.concat(fact.keyName);
                        }
                        return diffKeys;
                    }, []);
                return diffs;
            }, {});

        var factsWithDivergence =
             _.mapValues(itemsWithDiffs, function(fact) {
                var divergentKeys = keysWithDiffs[serializedFactKey(fact)];
                if (divergentKeys) {
                    var isDivergent = _.include(divergentKeys, fact.keyName);
                    return _.merge({}, fact, { isDivergent: isDivergent });
                } else {
                    return _.merge({}, fact, { isDivergent: false });
                }
            });

        return factsWithDivergence;

    }
}
