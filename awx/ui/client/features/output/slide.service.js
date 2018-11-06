/* eslint camelcase: 0 */
import {
    OUTPUT_MAX_BUFFER_LENGTH,
    OUTPUT_PAGE_SIZE,
} from './constants';

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

        return this.api.getRange(next);
    };

    this.getPrevious = (displacement = OUTPUT_PAGE_SIZE) => {
        const previous = this.getPreviousRange(displacement);

        return this.api.getRange(previous);
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

            if (count > OUTPUT_MAX_BUFFER_LENGTH) {
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

        this.buffer.events.length = 0;
        delete this.buffer.events;

        this.buffer.events = frames;
        this.buffer.min = min;
        this.buffer.max = max;
        this.buffer.count = count;

        if (tail - head === 0) {
            return frames;
        }

        return frames.filter(({ counter }) => counter > tail);
    };

    this.clear = () => {
        this.buffer.events.length = 0;
        this.buffer.min = 0;
        this.buffer.max = 0;
        this.buffer.count = 0;
    };

    this.getFrames = () => $q.resolve(this.buffer.events);

    this.getMaxCounter = () => {
        if (this.buffer.max && this.buffer.max > 1) {
            return this.buffer.max;
        }

        return this.api.getMaxCounter();
    };

    this.isOnLastPage = () => {
        if (this.buffer.min) {
            return this.getTailCounter() >= this.buffer.min - 1;
        }

        return this.getTailCounter() >= this.getMaxCounter() - OUTPUT_PAGE_SIZE;
    };

    this.isOnFirstPage = () => this.getHeadCounter() === 1;
    this.getTailCounter = () => this.storage.getTailCounter();
    this.getHeadCounter = () => this.storage.getHeadCounter();
}

SlidingWindowService.$inject = ['$q'];

export default SlidingWindowService;
