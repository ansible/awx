/**
 * Logout from the current session by clicking on the power off button on the
 * navigation menu.
 */
exports.command = function logout () {
    const logoutButton = '.at-Layout-topNav i.fa-power-off';
    this
        // protective wait for immediate login/logout
        .waitForElementNotPresent('.LoginModal-backDrop')
        .waitForElementNotVisible('.spinny')
        .findThenClick(logoutButton, 'css')
        .waitForElementPresent('#login-button');
};
