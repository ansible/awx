/* eslint camelcase: 0 */
import {
    OUTPUT_EVENT_LIMIT,
    OUTPUT_PAGE_SIZE,
} from './constants';

function getContinuous (events, reverse = false) {
    const counters = events.map(({ counter }) => counter);

    const min = Math.min(...counters);
    const max = Math.max(...counters);

    const missing = [];
    for (let i = min; i <= max; i++) {
        if (counters.indexOf(i) < 0) {
            missing.push(i);
        }
    }

    if (missing.length === 0) {
        return events;
    }

    if (reverse) {
        const threshold = Math.max(...missing);

        return events.filter(({ counter }) => counter > threshold);
    }

    const threshold = Math.min(...missing);

    return events.filter(({ counter }) => counter < threshold);
}

function SlidingWindowService ($q) {
    this.init = ({ getRange, getFirst, getLast, getMaxCounter }, storage) => {
        const { getHeadCounter, getTailCounter } = storage;

        this.api = {
            getRange,
            getFirst,
            getLast,
            getMaxCounter,
        };

        this.storage = {
            getHeadCounter,
            getTailCounter,
        };

        this.buffer = {
            events: [],
            min: 0,
            max: 0,
            count: 0,
        };

        this.cache = {
            first: null
        };
    };

    this.getBoundedRange = range => {
        const bounds = [1, this.getMaxCounter()];

        return [Math.max(range[0], bounds[0]), Math.min(range[1], bounds[1])];
    };

    this.getNextRange = displacement => {
        const tail = this.getTailCounter();

        return this.getBoundedRange([tail + 1, tail + 1 + displacement]);
    };

    this.getPreviousRange = displacement => {
        const head = this.getHeadCounter();

        return this.getBoundedRange([head - 1 - displacement, head - 1]);
    };

    this.getNext = (displacement = OUTPUT_PAGE_SIZE) => {
        const next = this.getNextRange(displacement);

        return this.api.getRange(next)
            .then(results => getContinuous(results));
    };

    this.getPrevious = (displacement = OUTPUT_PAGE_SIZE) => {
        const previous = this.getPreviousRange(displacement);

        return this.api.getRange(previous)
            .then(results => getContinuous(results, true));
    };

    this.getFirst = () => {
        if (this.cache.first) {
            return $q.resolve(this.cache.first);
        }

        return this.api.getFirst()
            .then(events => {
                if (events.length === OUTPUT_PAGE_SIZE) {
                    this.cache.first = events;
                }

                return $q.resolve(events);
            });
    };

    this.getLast = () => this.getFrames()
        .then(frames => {
            if (frames.length > 0) {
                return $q.resolve(frames);
            }

            return this.api.getLast();
        });

    this.pushFrames = events => {
        const head = this.getHeadCounter();
        const tail = this.getTailCounter();
        const frames = this.buffer.events.concat(events);

        let min;
        let max;
        let count = 0;

        for (let i = frames.length - 1; i >= 0; i--) {
            count++;

            if (count > OUTPUT_EVENT_LIMIT) {
                frames.splice(i, 1);

                count--;
                continue;
            }

            if (!min || frames[i].counter < min) {
                min = frames[i].counter;
            }

            if (!max || frames[i].counter > max) {
                max = frames[i].counter;
            }
        }

        this.buffer.events = frames;
        this.buffer.min = min;
        this.buffer.max = max;
        this.buffer.count = count;

        if (tail - head === 0) {
            return frames;
        }

        if (min >= head && min <= tail + 1) {
            return frames.filter(({ counter }) => counter > tail);
        }

        return [];
    };

    this.getFrames = () => $q.resolve(this.buffer.events);

    this.getMaxCounter = () => {
        if (this.buffer.min && this.buffer.min > 1) {
            return this.buffer.min - 1;
        }

        return this.api.getMaxCounter();
    };

    this.isOnLastPage = () => {
        if (this.getTailCounter() === 0) {
            return true;
        }

        return this.getTailCounter() >= (this.getMaxCounter() - OUTPUT_PAGE_SIZE);
    };

    this.isOnFirstPage = () => this.getHeadCounter() === 1;
    this.getTailCounter = () => this.storage.getTailCounter();
    this.getHeadCounter = () => this.storage.getHeadCounter();
}

SlidingWindowService.$inject = ['$q'];

export default SlidingWindowService;
