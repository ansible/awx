/* jshint node: true */

import '../../support/node';

import compareFacts from 'tower/system-tracking/compare-facts/nested';

describe('CompareFacts.Nested', function() {

    it('returns empty array with no fact data', function() {
        var result = compareFacts({ facts: [] }, { facts: [] });

        expect(result).to.deep.equal([]);
    });

    it('returns empty array when no differences', function() {
        var result = compareFacts(
                        {   facts:
                            {  'testing_facts':
                                    {   'foo': 'bar'
                                    }
                            }
                        },
                        {   facts:
                            {   'testing_facts':
                                    {   'foo': 'bar'
                                    }
                            }
                        });

        expect(result).to.deep.equal([]);
    });

    context('when only left set has data', function() {

        it('returns values with data for value1 and "absent" for value2', function() {

            var result = compareFacts(
                            {   position: 'left',
                                facts:
                                {  'testing_facts':
                                        {   'foo': 'bar'
                                        }
                                }
                            },
                            {   position: 'right',
                                facts:
                                {}
                            });

            expect(result[0].facts).to.contain
                .an.item
                .with.property('value1', 'bar');

            expect(result[0].facts).to.contain
                .an.item
                .with.property('value2', 'absent');

        });

    });

    context('when only right set has data', function() {

        it('returns values with data for value2 and "absent" for value1', function() {

            var result = compareFacts(
                            {   position: 'left',
                                facts:
                                {}
                            },
                            {   position: 'right',
                                facts:
                                {  'testing_facts':
                                        {   'foo': 'bar'
                                        }
                                }
                            });

            expect(result).not.to.be.empty;

            expect(result[0].facts).to.contain
                .an.item
                .with.property('value1', 'absent');

            expect(result[0].facts).to.contain
                .an.item
                .with.property('value2', 'bar');

        });

    });

    context('when both sets have fact data and differences exist', function() {

        it('does not consider false values "absent"', function() {
            var result = compareFacts(
                            {   position: 'left',
                                facts:
                                {   'testing_facts':
                                        {   'foo': false
                                        }
                                }
                            },
                            {   position: 'right',
                                facts:
                                {  'testing_facts':
                                        {   'foo': true
                                        }
                                }
                            });

            expect(result[0].facts).to.contain
                .an.item
                .with.property('value1', false);

            expect(result[0].facts).to.contain
                .an.item
                .with.property('value2', true);
        });

        it('uses "absent" for both values when neither has data', function() {
            var result = compareFacts(
                            {   position: 'left',
                                facts:
                                {   'testing_facts':
                                        {   'foo': 'baz',
                                            'blah': null
                                        }
                                }
                            },
                            {   position: 'right',
                                facts:
                                {  'testing_facts':
                                        {   'foo': 'bar',
                                            'blah': null
                                        }
                                }
                            });

            expect(result[0].facts).to.contain
                .an.item
                .with.property('value1', 'absent');

            expect(result[0].facts).to.contain
                .an.item
                .with.property('value2', 'absent');



        });
    });

});
