import '../support/node';

import {describeModule} from '../support/describe-module';
import mod from 'shared/multi-select-list/main';

var mockController = {
    selectAll: sinon.spy(),
    deselectAll: sinon.spy(),
    selectAllExtended: sinon.spy(),
    deselectAllExtended: sinon.spy()
};

describeModule(mod.name)
    .testDirective('selectAll', function(directive) {

        var $scope;

        directive.use('<fake-parent><select-all selections-empty="isEmpty" extended-items-length="numItems"></select-all></fake-parent>');

        beforeEach(function() {
            directive.element.data('$multiSelectListController', mockController);
        });

        afterEach(function() {
            mockController.selectAll.reset();
            mockController.deselectAll.reset();
            mockController.selectAllExtended.reset();
            mockController.deselectAllExtended.reset();
        });

        directive.afterCompile(function() {

            // Since we had to wrap select-all in a fake directive
            // to mock the controller, we have to reach down to
            // get it's isolate scope
            //
            $scope =
                directive.$element.find('select-all').isolateScope();
        });

        it('works as an element tag', function() {
            var classes = directive.$element.attr('class').split(' ');
            expect(classes).to.contain('ng-scope');
        });

        it('calls select all when isSelected is true', function() {
            $scope.isSelected = true;
            $scope.doSelectAll();
            expect(mockController.selectAll).to.have.been.calledOnce;
        });

        it('calls deselect all when isSelected is false', function() {
            $scope.isSelected = false;
            $scope.doSelectAll();

            expect(mockController.deselectAll).to.have.been.calledOnce;
        });

        it('calls deselect all extended when deselecting all', function() {
            $scope.isSelected = false;
            $scope.isSelectionExtended = true;
            $scope.doSelectAll();

            expect(mockController.deselectAllExtended).to.have.been.calledOnce;
        });

        context('input parameters', function() {

            var $outerScope;

            // We need to grab the parent scope object so we can control
            // the parameters that are passed into the directive in the
            // `use` call above
            directive.withScope(function(_outerScope) {
                $outerScope = _outerScope;
            });

            it('when true sets isSelected to false', function() {

                $scope.isSelected = true;
                $outerScope.isEmpty = true;
                $outerScope.$apply();

                expect($scope).to.have.property('isSelected', false);
            });

            it('sets supportsExtendedItems when extendedItemsLength is given', function() {
                $scope.supportsExtendedItems = false;
                $outerScope.numItems = 5;
                $outerScope.$apply();

                expect($scope).to.have.property('supportsExtendedItems', true);
            });


    });
});
