/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function wrapDelegate($delegate) {
    $delegate.hasModelKey = function hasModelKey(key) {
        return $delegate.params.hasOwnProperty('model') &&
            $delegate.params.model.hasOwnProperty(key);
    };

    return $delegate;
}

export default
    [   '$provide',
        function($provide) {
            $provide.decorator('$route', wrapDelegate);

        }
    ];
