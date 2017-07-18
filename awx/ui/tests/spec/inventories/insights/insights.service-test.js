'use strict';

import insights_json from './data/insights-data.js';
import solvable_insights_json from './data/solvable.insights-data.js';
import not_solvable_insights_json from './data/not_solvable.insights-data.js';
import high_insights_json from './data/high.insights-data.js';
import medium_insights_json from './data/medium.insights-data.js';
import low_insights_json from './data/low.insights-data.js';

describe('Service: InsightsService', () => {
    let InsightsService;

    beforeEach(angular.mock.module('awApp'));

    beforeEach(angular.mock.inject(( _InsightsService_) => {
        InsightsService = _InsightsService_;
    }));

    describe('filter()', () => {
        it('filter for "total" returns the total set of reports', () => {
            let filteredSet = InsightsService.filter('total', insights_json.reports);
            expect(filteredSet).toEqual(insights_json.reports);
            expect(filteredSet.length).toBe(12);
        });

        it('properly filters the reports dataset for solvable reports', () => {
            let filteredSet = InsightsService.filter('solvable', insights_json.reports);
            expect(filteredSet).toEqual(solvable_insights_json);
            expect(filteredSet.length).toBe(3);
        });

        it('properly filters the reports dataset for not-solvable reports', () => {
            let filteredSet = InsightsService.filter('not_solvable', insights_json.reports);
            expect(filteredSet).toEqual(not_solvable_insights_json);
            expect(filteredSet.length).toBe(9);
        });

        it('properly filters the reports dataset for CRITICAL reports', () => {
            let filteredSet = InsightsService.filter('critical', insights_json.reports);
            expect(filteredSet).toEqual([]);
            expect(filteredSet.length).toBe(0);
        });

        it('properly filters the reports dataset for ERROR reports', () => {
            let filteredSet = InsightsService.filter('high', insights_json.reports);
            expect(filteredSet).toEqual(high_insights_json);
            expect(filteredSet.length).toBe(2);
        });

        it('properly filters the reports dataset for WARN reports', () => {
            let filteredSet = InsightsService.filter('medium', insights_json.reports);
            expect(filteredSet).toEqual(medium_insights_json);
            expect(filteredSet.length).toBe(8);
        });

        it('properly filters the reports dataset for INFO reports', () => {
            let filteredSet = InsightsService.filter('low', insights_json.reports);
            expect(filteredSet).toEqual(low_insights_json);
            expect(filteredSet.length).toBe(2);
        });
    });
});
