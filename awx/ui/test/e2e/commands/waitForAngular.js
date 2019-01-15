import { AWX_E2E_TIMEOUT_ASYNC } from '../settings';

/* Post-login utility function that waits for the application to fully load. */
exports.command = function waitForAngular (callback) {
    this.timeoutsAsyncScript(AWX_E2E_TIMEOUT_ASYNC, () => {
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
