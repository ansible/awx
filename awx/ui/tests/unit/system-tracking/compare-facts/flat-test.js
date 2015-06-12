import compareFacts from 'tower/system-tracking/compare-facts/flat';

/* jshint node: true */
/* globals -expect, -_ */

var chai = require('chai');
var _ = require('lodash');
var chaiThings = require('chai-things');

chai.use(chaiThings);

global.expect = chai.expect;
global._ = _;

describe('CompareFacts.Flat', function() {

    function options(overrides) {
        return _.merge({}, defaultOptions, overrides);
    }

    var defaultTemplate =
        {   hasTemplate: function() { return false; }
        };

    var defaultOptions =
        {   factTemplate: defaultTemplate,
            nameKey: 'name'
        };

    it('returns empty array with empty basis facts', function() {
        var result = compareFacts({ facts: [] }, { facts: [] }, defaultOptions);

        expect(result).to.deep.equal([]);
    });

    it('returns empty array when no differences', function() {
        var result = compareFacts(
                        {   facts:
                            [{  'name': 'foo',
                                'value': 'bar'
                            }]
                        },
                        {   facts:
                            [{  'name': 'foo',
                                'value': 'bar'
                            }]
                        }, options({ nameKey: 'name',
                                     compareKey: ['value'],
                                   }));

        expect(result).to.deep.equal([]);
    });

    it('returns empty array with multiple compare keys and no differences', function() {
        var result = compareFacts(
                        {   facts:
                            [{  'name': 'foo',
                                'value': 'bar'
                            }]
                        },
                        {   facts:
                            [{  'name': 'foo',
                                'value': 'bar'
                            }]
                        }, options({    compareKey: ['name', 'value']
                                  }));

        expect(result).to.deep.equal([]);
    });

    context('when both collections contain facts', function() {
        it('includes each compare key value when a compareKey differs', function() {
            var result = compareFacts(
                            {   position: 'left',
                                facts:
                                [{  'name': 'foo',
                                    'value': 'bar',
                                    'extra': 'doo'
                                }]
                            },
                            {   position: 'right',
                                facts:
                                [{  'name': 'foo',
                                    'value': 'baz',
                                    'extra': 'doo'
                                }]
                            }, options({ compareKey: ['value', 'extra'] }));

            expect(result).to.deep.equal(
                [{  displayKeyPath: 'foo',
                    nestingLevel: 0,
                    facts:
                    [{  keyName: 'value',
                        value1: 'bar',
                        value1IsAbsent: false,
                        value2: 'baz',
                        value2IsAbsent: false,
                        isDivergent: true
                    },
                    {   keyName: 'extra',
                        value1: 'doo',
                        value1IsAbsent: false,
                        value2: 'doo',
                        value2IsAbsent: false,
                        isDivergent: false
                    }]
                }]);
        });

        it('ignores compare keys with no values in fact', function() {
            var result = compareFacts(
                            {   position: 'left',
                                facts:
                                [{  'name': 'foo',
                                    'value': 'bar',
                                    'extra': 'doo'
                                }]
                            },
                            {   position: 'right',
                                facts:
                                [{  'name': 'foo',
                                    'value': 'baz',
                                    'extra': 'doo'
                                }]
                            }, options({ compareKey: ['value', 'extra', 'blah'] }));

            expect(result).to.deep.equal(
                [{  displayKeyPath: 'foo',
                    nestingLevel: 0,
                    facts:
                    [{  keyName: 'value',
                        value1: 'bar',
                        value1IsAbsent: false,
                        value2: 'baz',
                        value2IsAbsent: false,
                        isDivergent: true
                    },
                    {   keyName: 'extra',
                        value1: 'doo',
                        value1IsAbsent: false,
                        value2: 'doo',
                        value2IsAbsent: false,
                        isDivergent: false
                    }]
                }]);

        });

        it('allows mapping key names with keyNameMap parameter', function() {
            var keyNameMap =
                {   'extra': 'blah'
                };

            var result = compareFacts(
                            {   position: 'left',
                                facts:
                                [{  'name': 'foo',
                                    'value': 'bar',
                                    'extra': 'doo'
                                }]
                            },
                            {   position: 'right',
                                facts:
                                [{  'name': 'foo',
                                    'value': 'baz',
                                    'extra': 'doo'
                                }]
                            }, options({    compareKey: ['value', 'extra', 'blah'],
                                            keyNameMap: keyNameMap
                                      }));

            expect(result[0].facts).to.include.something.that.deep.equals(
                    {   keyName: 'blah',
                        value1: 'doo',
                        value1IsAbsent: false,
                        value2: 'doo',
                        value2IsAbsent: false,
                        isDivergent: false
                    });

        });

        // it('allows formatting values with valueFormat parameter', function() {
        //     var valueFormat =
        //         function(key, values) {
        //             if (key === 'extra') {
        //                 return 'formatted';
        //             }
        //         }

        //     var result = compareFacts(
        //                     {   position: 'left',
        //                         facts:
        //                         [{  'name': 'foo',
        //                             'value': 'bar',
        //                             'extra': 'doo'
        //                         }]
        //                     },
        //                     {   position: 'right',
        //                         facts:
        //                         [{  'name': 'foo',
        //                             'value': 'baz',
        //                             'extra': 'doo'
        //                         }]
        //                     }, 'name', ['value', 'extra', 'blah'], keyNameMap, defaultTemplate, );

        //     expect(result[0].facts).to.include.something.that.deep.equals(
        //             {   keyName: 'extra',
        //                 value1: 'formatted',
        //                 value1IsAbsent: false,
        //                 value2: 'formatted',
        //                 value2IsAbsent: false,
        //                 isDivergent: false
        //             });

        // });

    });

    context('when value for nameKey is present in one collection but not the other', function() {

        function factData(leftFacts) {
            var facts = [{   position: 'left',
                            facts: leftFacts
                        },
                        {   position: 'right',
                            facts: []
                        }];

            return facts;
        }

        it('uses "absent" for the missing value', function() {

            var facts = factData([{  'name': 'foo',
                                     'value': 'bar'
                                 }]);

            var result = compareFacts(facts[0], facts[1],
                                      options({ compareKey: ['value']
                                             }));

            expect(result).to.deep.equal(
                [{  displayKeyPath: 'foo',
                    nestingLevel: 0,
                    facts:
                    [{  keyName: 'value',
                        value1: 'bar',
                        value1IsAbsent: false,
                        value2: 'absent',
                        value2IsAbsent: true,
                        isDivergent: true
                    }]
                }]);
        });

        it('includes given compare keys from basisFacts', function() {
            var facts = factData([{  'name': 'foo',
                                     'value': 'bar',
                                     'extra': 'doo'
                                 }]);

            var result = compareFacts(facts[0], facts[1],
                                      options({ compareKey: ['value', 'extra']
                                             }));

            expect(result).to.deep.equal(
                [{  displayKeyPath: 'foo',
                    nestingLevel: 0,
                    facts:
                    [{  keyName: 'value',
                        value1: 'bar',
                        value1IsAbsent: false,
                        value2: 'absent',
                        value2IsAbsent: true,
                        isDivergent: true
                     },
                     {  keyName: 'extra',
                        value1: 'doo',
                        value1IsAbsent: false,
                        value2: 'absent',
                        value2IsAbsent: true,
                        isDivergent: true
                     }]
                }]);

        });

        context('with factTemplate', function() {
            it('does not attempt to render the absent fact', function() {
                var facts = factData([{  'name': 'foo'
                                     }]);

                var renderCallCount = 0;
                var factTemplate =
                    {   render: function() {
                                    renderCallCount++;
                                },
                        hasTemplate: function() { return true; },
                        template: ""
                    };

                compareFacts(facts[0], facts[1],
                             options({  compareKey: ['value'],
                                        factTemplate: factTemplate
                                    }));

                expect(renderCallCount).to.equal(1);

            });
        });
    });

    context('with factTemplate', function() {
        var factData;

        beforeEach(function() {
            factData = [{   position: 'left',
                            facts:
                            [{  'name': 'foo',
                                'value': 'bar'
                            }]
                        },
                        {   position: 'right',
                            facts:
                            [{  'name': 'foo',
                                'value': 'baz'
                            }]
                        }];
        });

        it('renders the template with each provided fact', function() {

            var renderCalledWith = [];
            var factTemplate =
                {   render: function(fact) {
                                renderCalledWith.push(fact);
                            },
                    hasTemplate: function() { return true; },
                    template: ""
                };

            compareFacts(factData[0], factData[1],
                         options({  compareKey: ['value'],
                                    factTemplate: factTemplate
                                 }));

            expect(renderCalledWith).to.include(factData[0].facts[0]);
            expect(renderCalledWith).to.include(factData[1].facts[0]);
        });


    });
});
