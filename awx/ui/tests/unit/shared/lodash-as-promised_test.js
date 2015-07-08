import '../setup-browser';

import 'tower/shared/main';

describe('LodashAsPromised', function() {

    var _;
    var $q;

    function addOne(num) {
        return num + 1;
    }

    function isEven(value) {
        return value % 2 === 0;
    }

    function sum(memo, value) {
        return memo + value;
    }

    beforeEach(window.module('shared'));

    beforeEach(inject(['lodashAsPromised', '$q', function(_lodash, _$q) {
        _ = _lodash;
        $q = _$q;
    }]));

    function checkPromiseAndArray(fnName, cb, coll, result) {
        context(fnName, function() {
            // var itFn = fnName === 'compact' ? it : xit;
            var itFn = it;

            itFn('works with a promise', function() {
                var values = coll.map($q.when);
                var methodName = 'then' + _.capitalize(fnName);
                var promise;
                // _.log('promises for _', values);
                if (fnName === 'reduce') {
                    promise = _[methodName](values, cb, 0);
                } else {
                    promise = _[methodName](values, cb);
                }

                inject(['$rootScope', function($rootScope) {
                    setTimeout(function() {
                        $rootScope.$apply();
                    }, 1);
                }]);

                return expect(promise).to.eventually.deep.equal(result);
            });

            itFn('works with an array', function() {
                var value = _[fnName](coll, cb, 0);
                expect(value).to.deep.equal(result);
            });
        });
    }

    checkPromiseAndArray('map', addOne, [1,2,3,4], [2,3,4,5]);
    checkPromiseAndArray('filter', isEven, [1,2,3,4,5,6,7,8], [2,4,6,8]);
    checkPromiseAndArray('reduce', sum, [1,2,3,4], 10);
    checkPromiseAndArray('pluck', 'blah', [{ blah: 'diddy' }, { blah: 'doo' }], ['diddy', 'doo']);
    checkPromiseAndArray('compact', null, ['blah', null, 'diddy', false, 'doo', undefined], ['blah', 'diddy', 'doo']);
    checkPromiseAndArray('xor', [4,2], [1,2], [1,4]);
    checkPromiseAndArray('groupBy', Math.floor, [4.2,6.1,6.4],  { '4': [4.2], '6': [6.1,6.4] } );

    it('allows chaining', function() {
        function dub(n) { return n * 2; }

        var arr = [1,2,3,4].map($q.when);

        expect(_(arr).thenMap(dub)).to.eventually.deep.equal([2,4,6,8]);
    });

});
