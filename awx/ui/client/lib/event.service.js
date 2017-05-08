function listenWith (scope) {
    return fn => apply(scope, fn);
}

function apply (scope, fn) {
    return () => scope.$apply(fn);
}

function EventService () {
    return {
        listenWith,
        apply
    };
}

export default EventService;
