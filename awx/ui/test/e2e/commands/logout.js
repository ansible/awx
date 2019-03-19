/**
 * Logout from the current session by clicking on the power off button on the
 * navigation menu.
 */
exports.command = function logout () {
    const logoutButton = '.at-Layout-topNav i.fa-power-off';
    this
        .waitForElementVisible(logoutButton)
        .click(logoutButton)
        .waitForElementPresent('#login-button');
};
