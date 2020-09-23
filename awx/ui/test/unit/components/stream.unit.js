import StreamService from '~features/output/stream.service';

describe('Output | StreamService', () => {
    angular.module('test', []).service('StreamService', StreamService);
    let stream;

    beforeEach(() => {
        angular.mock.module('test');
    });

    beforeEach(angular.mock.inject(($injector) => {
        stream = $injector.get('StreamService');

        const onFrames = angular.noop;
        const onFrameRate = angular.noop;

        stream.init({ onFrames, onFrameRate });
    }));

    describe('calcFactors', () => {
        it('returns the expected values', () => {
            const params = [
                [-1, [1]],
                [0, [1]],
                [1, [1]],
                [1.0, [1]],
                [1.1, [1]],
                [2, [1, 2]],
                ['1', [1]],
                [{}, [1]],
                [null, [1]],
                [undefined, [1]],
                [250, [1, 2, 5, 10, 25, 50, 125, 250]]
            ];

            params.forEach(([size, expected]) =>
                expect(stream.calcFactors(size)).toEqual(expected));
        });
    });

    describe('setMissingCounterThreshold', () => {
        it('returns the correct counter threshold', () => {
            const gt = 2;
            stream.setMissingCounterThreshold(gt);
            expect(stream.counters.min).toEqual(gt);

            const lt = -1;
            stream.setMissingCounterThreshold(lt);
            expect(stream.counters.min).toEqual(gt);
        });
    });

    describe('isReadyToRender', () => {
        it("it's never ready to render when live updates are enabled unless the result of getReadyCount is greater than 0", () => {
            delete window.liveUpdates;
            Object.defineProperty(window, 'liveUpdates', {
                value: true,
                writable: false
            });

            const params = [
                [-1, false],
                [0, false],
                [1, true]
            ];
            const spy = spyOn(stream, 'getReadyCount');

            params.forEach(([readyCount, expected]) => {
                spy.and.returnValue(readyCount);
                expect(stream.isReadyToRender()).toEqual(expected);
            });
        });
    });

    describe('getMaxCounter', () => {
        it('returns the same value as max counter', () => {
            const res = stream.getMaxCounter();
            expect(res).toEqual(stream.counters.max);
        });
    });

    describe('getReadyCount', () => {
        it('references min and max counters', () => {
            expect(stream.getReadyCount()).toEqual(stream.counters.max - stream.counters.min + 1);
        });
        it('returns expected values if min or max value is a non-integer', () => {
            const params = [
                [null, 1, 0],
                [undefined, 1, NaN],
                ['1', 1, 1],
                [-1, -3, 3],
                [0, 0, 1],
                [6, 5, 2]
            ];

            params.forEach(([max, min, expected]) => {
                stream.counters.ready = max;
                stream.counters.min = min;
                expect(stream.getReadyCount()).toEqual(expected);
            });
        });
    });
});
