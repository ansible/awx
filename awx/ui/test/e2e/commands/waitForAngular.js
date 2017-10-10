exports.command = function waitForAngular (callback) {
    this.timeoutsAsyncScript(this.globals.asyncHookTimeout, () => {
        this.executeAsync(done => {
            if (angular && angular.getTestability) {
                angular.getTestability(document.body).whenStable(done);
            } else {
                done();
            }
        }, [], result => {
            if (typeof callback === 'function') {
                callback.call(this, result);
            }
        });
    });

    return this;
};
