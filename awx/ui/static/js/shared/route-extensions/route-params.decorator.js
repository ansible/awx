export function wrapDelegate($delegate) {
    $delegate.hasModelKey = function hasModelKey(key) {
        return $delegate.hasOwnProperty('model') &&
            $delegate.model.hasOwnProperty(key);
    };

    return $delegate;
}

export default
    [   '$provide',
        function($provide) {
            $provide.decorator('$routeParams', wrapDelegate);

        }
    ];
