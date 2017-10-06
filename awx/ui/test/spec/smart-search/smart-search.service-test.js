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

    describe('fn splitFilterIntoTerms', () => {
        it('should convert the filter term to a key and value with encode quotes and spaces', () => {
            expect(SmartSearchService.splitFilterIntoTerms()).toEqual(null);
            expect(SmartSearchService.splitFilterIntoTerms('foo')).toEqual(["foo"]);
            expect(SmartSearchService.splitFilterIntoTerms('foo bar')).toEqual(["foo", "bar"]);
            expect(SmartSearchService.splitFilterIntoTerms('name:foo bar')).toEqual(["name:foo", "bar"]);
            expect(SmartSearchService.splitFilterIntoTerms('name:foo description:bar')).toEqual(["name:foo", "description:bar"]);
            expect(SmartSearchService.splitFilterIntoTerms('name:"foo bar"')).toEqual(["name:%22foo%20bar%22"]);
            expect(SmartSearchService.splitFilterIntoTerms('name:"foo bar" description:"bar foo"')).toEqual(["name:%22foo%20bar%22", "description:%22bar%20foo%22"]);
            expect(SmartSearchService.splitFilterIntoTerms('name:"foo bar" a b c')).toEqual(["name:%22foo%20bar%22", 'a', 'b', 'c']);
            expect(SmartSearchService.splitFilterIntoTerms('name:"1"')).toEqual(["name:%221%22"]);
            expect(SmartSearchService.splitFilterIntoTerms('name:1')).toEqual(["name:1"]);
            expect(SmartSearchService.splitFilterIntoTerms('name:"foo ba\'r" a b c')).toEqual(["name:%22foo%20ba%27r%22", 'a', 'b', 'c']);
            expect(SmartSearchService.splitFilterIntoTerms('name:"foobar" other:"barbaz"')).toEqual(["name:%22foobar%22", "other:%22barbaz%22"]);
            expect(SmartSearchService.splitFilterIntoTerms('name:"foobar" other:"bar baz"')).toEqual(["name:%22foobar%22", "other:%22bar%20baz%22"]);
        });
    });

});
