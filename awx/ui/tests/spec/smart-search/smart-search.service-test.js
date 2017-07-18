'use strict';

describe('Service: SmartSearch', () => {
    let SmartSearchService;

    beforeEach(angular.mock.module('awApp'));

    beforeEach(angular.mock.module('SmartSearchModule'));

    beforeEach(angular.mock.inject((_SmartSearchService_) => {
        SmartSearchService = _SmartSearchService_;
    }));

    describe('fn splitSearchIntoTerms', () => {
        it('should convert the search string to an array tag strings', () =>{
            expect(SmartSearchService.splitSearchIntoTerms('foo')).toEqual(["foo"]);
            expect(SmartSearchService.splitSearchIntoTerms('foo bar')).toEqual(["foo", "bar"]);
            expect(SmartSearchService.splitSearchIntoTerms('name:foo bar')).toEqual(["name:foo", "bar"]);
            expect(SmartSearchService.splitSearchIntoTerms('name:foo description:bar')).toEqual(["name:foo", "description:bar"]);
            expect(SmartSearchService.splitSearchIntoTerms('name:"foo bar"')).toEqual(["name:\"foo bar\""]);
            expect(SmartSearchService.splitSearchIntoTerms('name:"foo bar" description:"bar foo"')).toEqual(["name:\"foo bar\"", "description:\"bar foo\""]);
            expect(SmartSearchService.splitSearchIntoTerms('name:"foo bar"       description:"bar foo"')).toEqual(["name:\"foo bar\"", "description:\"bar foo\""]);
            expect(SmartSearchService.splitSearchIntoTerms('name:\'foo bar\'')).toEqual(["name:\'foo bar\'"]);
            expect(SmartSearchService.splitSearchIntoTerms('name:\'foo bar\' description:\'bar foo\'')).toEqual(["name:\'foo bar\'", "description:\'bar foo\'"]);
            expect(SmartSearchService.splitSearchIntoTerms('name:\'foo bar\'       description:\'bar foo\'')).toEqual(["name:\'foo bar\'", "description:\'bar foo\'"]);
            expect(SmartSearchService.splitSearchIntoTerms('name:\"foo bar\" description:\'bar foo\'')).toEqual(["name:\"foo bar\"", "description:\'bar foo\'"]);
            expect(SmartSearchService.splitSearchIntoTerms('name:\"foo bar\" foo')).toEqual(["name:\"foo bar\"", "foo"]);
            expect(SmartSearchService.splitSearchIntoTerms('inventory:¯\_(ツ)_/¯')).toEqual(["inventory:¯\_(ツ)_/¯"]);
            expect(SmartSearchService.splitSearchIntoTerms('inventory:¯\_(ツ)_/¯ inventory.name:¯\_(ツ)_/¯')).toEqual(["inventory:¯\_(ツ)_/¯", "inventory.name:¯\_(ツ)_/¯"]);
        });
    });

    describe('fn splitTermIntoParts', () => {
        it('should convert the search term to a key and value', () =>{
            expect(SmartSearchService.splitTermIntoParts('foo')).toEqual(["foo"]);
            expect(SmartSearchService.splitTermIntoParts('foo:bar')).toEqual(["foo", "bar"]);
            expect(SmartSearchService.splitTermIntoParts('foo:bar:foobar')).toEqual(["foo", "bar:foobar"]);
            expect(SmartSearchService.splitTermIntoParts('name:\"foo bar\"')).toEqual(["name", "\"foo bar\""]);
            expect(SmartSearchService.splitTermIntoParts('name:\"foo:bar\"')).toEqual(["name", "\"foo:bar\""]);
            expect(SmartSearchService.splitTermIntoParts('name:\'foo bar\'')).toEqual(["name", "\'foo bar\'"]);
            expect(SmartSearchService.splitTermIntoParts('name:\'foo:bar\'')).toEqual(["name", "\'foo:bar\'"]);
        });
    });

});
