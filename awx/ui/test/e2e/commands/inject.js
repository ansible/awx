exports.command = function inject (deps, script, callback) {
    this.executeAsync(
        `let args = Array.prototype.slice.call(arguments,0);

        return function(deps, done) {
            let injector = angular.element('body').injector();
            let loaded = deps.map(d => {
                if (typeof(d) === "string") {
                    return injector.get(d);
                } else {
                    return d;
                }
            });
            (${script.toString()}).apply(this, loaded).then(done);
        }.apply(this, args);`,
        [deps],
        function handleResult (result) {
            if (typeof callback === 'function') {
                callback.call(this, result.value);
            }
        }
    );

    return this;
};
