import '../support/node';

import {describeModule} from '../support/describe-module';
import mod from '../../src/shared/multi-select-list/main';

describeModule(mod.name)
    .testDirective('multiSelectList', function(test) {

        var $scope;
        var controller;

        test.use('<div multi-select-list></div>');

        test.afterCompile(function(outerScope, scope) {
            $scope = scope;
        });

        test.withController(function(_controller) {
            controller = _controller;
        });

        it('works as an attribute on elements', function() {
            window.inject(['$compile', function($compile) {
                var node = $compile('<div multi-select-list></div>')($scope);
                var classes = Array.prototype.slice.apply(node.attr('class').split(' '));
                expect(classes).to.contain('ng-scope');
           }]);
        });

        context('controller init', function() {

            it('initializes items and selection', function() {
               expect($scope.items).to.be.empty;
               expect($scope.selection.selectedItems).to.be.empty;
               expect($scope.selection.deselectedItems).to.be.empty;
               expect($scope.selection.isExtended).to.be.false;
            });

            it('wraps items when they are registered', function() {
                var item = { name: 'blah' };
                var wrapped = controller.registerItem(item);

                expect(wrapped.hasOwnProperty('isSelected')).to.be.true;
                expect(wrapped.hasOwnProperty('value')).to.be.true;

                expect(wrapped.isSelected).to.be.false;
                expect(wrapped.value).to.eql(item);

            });

        });

        context('single select/deselect', function() {

            it('marks item as selected/not selected', function() {
                var item = controller.registerItem({ name: 'blah' });
                controller.selectItem(item);

                expect(item.isSelected).to.be.true;

                controller.deselectItem(item);
                expect(item.isSelected).to.be.false;
            });

            context('selectionChanged event', function() {

                it('triggers on select/deselect', function() {
                    var item = controller.registerItem({ name: 'blah' });
                    var spy = sinon.spy();

                    $scope.$on('multiSelectList.selectionChanged', spy);

                    controller.selectItem(item);
                    controller.deselectItem(item);

                    expect(spy).to.have.been.calledTwice;
                });

                it('is called with the current selection', function() {
                    var item = controller.registerItem({ name: 'blah' });
                    var spy = sinon.spy();

                    $scope.$on('multiSelectList.selectionChanged', spy);

                    controller.selectItem(item);

                    expect(spy).to.have.been.calledWith(sinon.match.object,
                        {   selectedItems:
                                [   item.value
                                ],
                            deselectedItems: [],
                            isExtended: false
                        });
                });

                it('is called with deselections', function() {
                    var item = controller.registerItem({ name: 'blah' });
                    controller.selectItem(item);

                    var spy = sinon.spy();


                    $scope.$on('multiSelectList.selectionChanged', spy);
                    controller.deselectItem(item);

                    expect(spy).to.have.been.calledWith(sinon.match.object,
                        {   selectedItems: [],
                            deselectedItems:
                                [   item.value
                                ],
                            isExtended: false
                        });
                });

            });

        });

        context('select/deselect all items', function() {

            it('marks all items as selected/deselected', function() {
                var item1 = controller.registerItem({ name: 'blah' });
                var item2 = controller.registerItem({ name: 'diddy' });
                var item3 = controller.registerItem({ name: 'doo' });

                controller.selectAll();

                expect([item1, item2, item3]).to.all.have.property('isSelected', true);

                controller.deselectAll();

                expect([item1, item2, item3]).to.all.have.property('isSelected', false);
            });

            context('selectionChanged event', function() {

                it('triggers with selections set to all the items', function() {
                    var item1 = controller.registerItem({ name: 'blah' });
                    var item2 = controller.registerItem({ name: 'diddy' });
                    var item3 = controller.registerItem({ name: 'doo' });
                    var spy = sinon.spy();

                    $scope.$on('multiSelectList.selectionChanged', spy);

                    controller.selectAll();

                    expect(spy).to.have.been.calledWith(
                        sinon.match.object,
                        {   selectedItems: _.pluck([item1, item2, item3], "value"),
                            deselectedItems: [],
                            isExtended: false
                        });

                    controller.deselectAll();

                    expect(spy).to.have.been.calledWith(
                        sinon.match.object,
                        {   selectedItems: [],
                            deselectedItems: _.pluck([item1, item2, item3], "value"),
                            isExtended: false
                        });

                });

            });


            it('tracks extended selection state', function() {
                var spy = sinon.spy();
                var item1 = controller.registerItem({ name: 'blah' });
                var item2 = controller.registerItem({ name: 'diddy' });
                var item3 = controller.registerItem({ name: 'doo' });
                var allItems = _.pluck([item1, item2, item3], 'value');

                controller.selectAll();
                controller.selectAllExtended();

                expect($scope.selection).to.have.property('isExtended', true);

                controller.deselectAllExtended();

                expect($scope.selection).to.have.property('isExtended', false);
                expect($scope.selection)
                        .to.have.property('selectedItems')
                        .that.is.an('array')
                        .deep.equals(allItems);
            });


            it('toggles extended state on deselectAll', function() {
                controller.selectAllExtended();

                controller.deselectAll();

                expect($scope.selection).to.have.property('isExtended', false);
            });
        });
    });

