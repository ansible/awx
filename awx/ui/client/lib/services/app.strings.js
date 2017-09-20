/**
 * This service is used to access the app-wide strings defined in BaseStringService.
 */
function AppStrings (BaseString) {
    BaseString.call(this, 'app');
}

AppStrings.$inject = ['BaseStringService'];

export default AppStrings;
