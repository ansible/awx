/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import compareNestedFacts from './compare-facts/nested';
import compareFlatFacts from './compare-facts/flat';

export function compareFacts(module, facts) {
    if (module.displayType === 'nested') {
        return compareNestedFacts(facts);
    } else {
        return compareFlatFacts(facts, module.nameKey, module.compareKey);
    }
}
