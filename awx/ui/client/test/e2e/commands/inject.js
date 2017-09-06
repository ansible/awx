exports.command = function(deps, script, callback) {
    let self = this;
    this.executeAsync(`let args = Array.prototype.slice.call(arguments,0);
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
    function(result) {
        if(typeof(callback) === "function") {
            callback.call(self, result.value);
        }
    });
    return this;
};
