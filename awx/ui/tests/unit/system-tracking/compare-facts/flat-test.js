import compareFacts from 'tower/system-tracking/compare-facts/flat';

/* jshint node: true */
/* globals -expect, -_ */

var _, expect;

// This makes this test runnable in node OR karma. The sheer
// number of times I had to run this test made the karma
// workflow just too dang slow for me. Maybe this can
// be a pattern going forward? Not sure...
//
(function(global) {
    var chai = global.chai || require('chai');

    if (typeof window === 'undefined') {
        var chaiThings = global.chaiThings || require('chai-things');
        chai.use(chaiThings);
    }

    _ = global._ || require('lodash');
    expect = global.expect || chai.expect;

    global.expect = expect;



    global._ = _;

})(typeof window === 'undefined' ? global : window);

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
                    containsValueArray: false,
                    nestingLevel: 0,
                    facts:
                    [{  keyName: 'value',
                        value1: 'bar',
                        value2: 'baz',
                        isDivergent: true
                    },
                    {   keyName: 'extra',
                        value1: 'doo',
                        value2: 'doo',
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
                    containsValueArray: false,
                    nestingLevel: 0,
                    facts:
                    [{  keyName: 'value',
                        value1: 'bar',
                        value2: 'baz',
                        isDivergent: true
                    },
                    {   keyName: 'extra',
                        value1: 'doo',
                        value2: 'doo',
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
                        value2: 'doo',
                        isDivergent: false
                    });

        });

        it('allows flattening values with factTemplate parameter', function() {
            var factTemplate =
                {   hasTemplate:
                        function() {
                            return true;
                        },
                    render: function(fact) {
                        return 'value: ' + fact.value;
                    }
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
                            }, options({    compareKey: ['value'],
                                            factTemplate: factTemplate
                                      }));

            expect(result[0].facts).to.deep.equal(
                    {   keyName: 'foo',
                        value1: 'value: bar',
                        value2: 'value: baz'
                    });
        });

        it('allows formatting values with factTemplate parameter', function() {
            var values = ['value1', 'value2'];
            var factTemplate =
                {   'value':
                        {   hasTemplate: function() {
                                return true;
                            },
                            render: function() {
                                return values.shift();
                            }
                        },
                    'extra': true
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
                            }, options({    compareKey: ['value'],
                                            factTemplate: factTemplate
                                      }));

            expect(result[0].facts).to.include.something.that.deep.equals(
                    {   keyName: 'value',
                        value1: 'value1',
                        value2: 'value2',
                        isDivergent: true
                    },
                    {   keyName: 'extra',
                        value1: 'doo',
                        value2: 'doo',
                        isDivergent: false
                    });

        });

        it('compares values using the formatted values, not the raw ones', function() {
            var values = ['value1', 'value2'];
            var factTemplate =
                {   'extra':
                        {   render: function() {
                                return values.shift();
                            }
                        }
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
                                    'value': 'bar',
                                    'extra': 'doo'
                                }]
                            }, options({    factTemplate: factTemplate,
                                            compareKey: ['extra']
                                      }));

            expect(result.length).to.be.greaterThan(0);
            expect(result[0].facts).to.include.something.that.deep.equals(
                    {   keyName: 'extra',
                        value1: 'value1',
                        value2: 'value2',
                        isDivergent: true
                    });

        });

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

        it('keeps missing values as undefined', function() {

            var facts = factData([{  'name': 'foo',
                                     'value': 'bar'
                                 }]);

            var result = compareFacts(facts[0], facts[1],
                                      options({ compareKey: ['value']
                                             }));

            expect(result).to.deep.equal(
                [{  displayKeyPath: 'foo',
                    containsValueArray: false,
                    nestingLevel: 0,
                    facts:
                    [{  keyName: 'value',
                        value1: 'bar',
                        value2: undefined,
                        isDivergent: true
                    }]
                }]);
        });

        it('still keeps missing values as undefined when using a template', function() {

            var factTemplate =
                {   hasTemplate:
                        function() {
                            return true;
                        },
                    render:
                        function(fact) {
                            return fact.value;
                        }
                };

            var facts = factData([{  'name': 'foo',
                                     'value': 'bar'
                                 }]);

            var result = compareFacts(facts[0], facts[1],
                                      options({ compareKey: ['value'],
                                                factTemplate: factTemplate
                                             }));

            expect(result).to.deep.equal(
                [{  displayKeyPath: 'foo',
                    containsValueArray: false,
                    nestingLevel: 0,
                    facts:
                        {   keyName: 'foo',
                            value1: 'bar',
                            value2: undefined
                        }
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
                    containsValueArray: false,
                    nestingLevel: 0,
                    facts:
                    [{  keyName: 'value',
                        value1: 'bar',
                        value2: undefined,
                        isDivergent: true
                     },
                     {  keyName: 'extra',
                        value1: 'doo',
                        value2: undefined,
                        isDivergent: true
                     }]
                }]);

        });

    });

    describe('when value for nameKey exists multiple times in a single collection', function() {

        context('with differences between any of the values', function() {

            it('includes rendered values as array for value properties', function() {

                var factTemplate =
                    {   hasTemplate:
                            function() {
                                return true;
                            },
                        render: function(fact) {
                            return fact.version;
                        }
                };

                var result = compareFacts(
                                {   position: 'left',
                                    facts:
                                    [{  'name': 'some-package',
                                        'version': 'abcd'
                                    },
                                    {   'name': 'some-package',
                                        'version': 'efgh'
                                    }]
                                },
                                {   position: 'right',
                                    facts:
                                    [{  'name': 'some-package',
                                        'version': 'abcd'
                                    },
                                    {   'name': 'some-package',
                                        'version': 'ijkl'
                                    }]

                                }, options({    compareKey: ['value'],
                                                factTemplate: factTemplate,
                                                supportsValueArray: true
                                          }));

                expect(result[0].containsValueArray).to.equal(true);
                expect(result[0].facts).to.deep.equal(
                        {   keyName: 'some-package',
                            value1: ['abcd', 'efgh'],
                            value2: ['abcd', 'ijkl']
                        });
                });

        });

        context('with no differences between any of the values', function() {

            it('does not include the property at all', function() {
                var expectation;
                var factTemplate =
                    {   hasTemplate:
                            function() {
                                return true;
                            },
                        render: function(fact) {
                            return fact.version;
                        }
                };

                var result = compareFacts(
                                {   position: 'left',
                                    facts:
                                    [{  'name': 'some-package',
                                        'version': 'abcd'
                                    },
                                    {   'name': 'some-package',
                                        'version': 'efgh'
                                    }]
                                },
                                {   position: 'right',
                                    facts:
                                    [{  'name': 'some-package',
                                        'version': 'abcd'
                                    },
                                    {   'name': 'some-package',
                                        'version': 'efgh'
                                    }]

                                }, options({    compareKey: ['value'],
                                                factTemplate: factTemplate,
                                                supportsValueArray: true
                                          }));

                // Use assignment to avoid jshint warning
                expectation = expect(result).to.be.empty;
            });

            it('is insensitive to the order of the facts', function() {
                var expectation;
                var factTemplate =
                    {   hasTemplate:
                            function() {
                                return true;
                            },
                        render: function(fact) {
                            return fact.version;
                        }
                };

                var result = compareFacts(
                                {   position: 'left',
                                    facts:
                                    [{  'name': 'some-package',
                                        'version': 'efgh'
                                    },
                                    {   'name': 'some-package',
                                        'version': 'abcd'
                                    }]
                                },
                                {   position: 'right',
                                    facts:
                                    [{  'name': 'some-package',
                                        'version': 'abcd'
                                    },
                                    {   'name': 'some-package',
                                        'version': 'efgh'
                                    }]

                                }, options({    compareKey: ['value'],
                                                factTemplate: factTemplate,
                                                supportsValueArray: true
                                          }));

                // Use assignment to avoid jshint warning
                expectation = expect(result).to.be.empty;
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
