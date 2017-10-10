exports.command = function(callback) {
    let self = this;
    this.timeoutsAsyncScript(this.globals.asyncHookTimeout, function() {
        this.executeAsync(function(done) {
            if(angular && angular.getTestability) {
                angular.getTestability(document.body).whenStable(done);
            }
            else {
                done();
            }
        },
        [],
        function(result) {
            if(typeof(callback) === "function") {
                callback.call(self, result);
            }
        });
    });
    return this;
};
