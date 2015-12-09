import '../support/node';

describe("mainMenuTemplate", function() {

    // Define local variables.  The template path is basically the key
    // used as a reference to track the template within the $templateCache;
    var viewHtml;
    var templateUrl = '/static/main-menu/main-menu.partial.html';
    var $rootScope;
    var $scope;
    var $compile;
    var mainMenuElement;

    // The templates module gets defined during the build process
    // and including it gives us access to the templates that get
    // stuffed into $templateCache
    beforeEach("instantiate the templates module", function() {
        angular.mock.module("templates");
    });

    beforeEach(inject(function($templateCache) {
        // All of our templates should have been pre-loaded into $templateCache
        // during the build process.  Leverage $templateCache.get to retrieve
        // it into memory
        viewHtml = $templateCache.get(templateUrl);
    }));

    beforeEach(inject(function(_$compile_, _$rootScope_){
        $compile = _$compile_;
        $rootScope = _$rootScope_;
        $scope = $rootScope.$new();

        // If we needed to stub any scope variables we could do it here

        // Wrap HTML string as jQuery object
        mainMenuElement = angular.element(viewHtml);
    }));

    it('mobile menu items match non-mobile menu items', function() {
        compileElement();
        var mobileMenuItems = mainMenuElement.find("#main_menu_mobile_items > .MainMenu-item").length;
        var nonMobileMenuItems = mainMenuElement.find(".MainMenu-item--notMobile").length;
        expect(mobileMenuItems).to.equal(nonMobileMenuItems);
    });

    function compileElement() {
      $compile(mainMenuElement)($scope);
      $rootScope.$digest();
    }

});
