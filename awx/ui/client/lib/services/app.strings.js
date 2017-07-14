// The purpose of this file is to instantiate the BaseStringService
// for app-wide usage. 
function AppStrings (BaseString) {
    BaseString.call(this, 'app');
}

AppStrings.$inject = ['BaseStringService'];

export default AppStrings;
