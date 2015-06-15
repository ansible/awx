/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import compareNestedFacts from './compare-facts/nested';
import compareFlatFacts from './compare-facts/flat';
import FactTemplate from './compare-facts/fact-template';

export function compareFacts(module, facts) {


    var renderOptions = _.merge({}, module);

    // If the module has a template or includes a list of keys to display,
    // then perform a flat comparison, otherwise assume nested
    //
    if (renderOptions.factTemplate || renderOptions.nameKey) {
        // For flat structures we compare left-to-right, then right-to-left to
        // make sure we get a good comparison between both hosts

        if (_.isPlainObject(renderOptions.factTemplate)) {
            renderOptions.factTemplate =
                _.mapValues(renderOptions.factTemplate, function(template) {
                    if (typeof template === 'string' || typeof template === 'function') {
                        return new FactTemplate(template);
                    } else {
                        return template;
                    }
                });
        } else {
            renderOptions.factTemplate = new FactTemplate(renderOptions.factTemplate);
        }

        var leftToRight = compareFlatFacts(facts[0], facts[1], renderOptions);
        var rightToLeft = compareFlatFacts(facts[1], facts[0], renderOptions);

        return _(leftToRight)
                    .concat(rightToLeft)
                    .unique('displayKeyPath')
                    .thru(function(result) {
                        return  {   factData: result,
                                    isNestedDisplay: _.isPlainObject(renderOptions.factTemplate)
                                };
                    })
                    .value();
    } else {
        return {    factData: compareNestedFacts(facts),
                    isNestedDisplay: true
               };
    }
}
