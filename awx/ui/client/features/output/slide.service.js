/* eslint camelcase: 0 */
import {
    API_MAX_PAGE_SIZE,
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
    this.init = (storage, api, { getScrollHeight }) => {
        const { prepend, append, shift, pop, getRecord, deleteRecord, clear } = storage;
        const { getRange, getFirst, getLast, getMaxCounter } = api;

        this.api = {
            getRange,
            getFirst,
            getLast,
            getMaxCounter,
        };

        this.storage = {
            clear,
            prepend,
            append,
            shift,
            pop,
            getRecord,
            deleteRecord,
        };

        this.hooks = {
            getScrollHeight,
        };

        this.lines = {};
        this.uuids = {};
        this.chain = $q.resolve();

        this.state = { head: null, tail: null };
        this.cache = { first: null };

        this.buffer = {
            events: [],
            min: 0,
            max: 0,
            count: 0,
        };
    };

    this.getBoundedRange = range => {
        const bounds = [0, this.getMaxCounter()];

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

    this.createRecord = ({ counter, uuid, start_line, end_line }) => {
        this.lines[counter] = end_line - start_line;
        this.uuids[counter] = uuid;

        if (this.state.tail === null) {
            this.state.tail = counter;
        }

        if (counter > this.state.tail) {
            this.state.tail = counter;
        }

        if (this.state.head === null) {
            this.state.head = counter;
        }

        if (counter < this.state.head) {
            this.state.head = counter;
        }
    };

    this.deleteRecord = counter => {
        this.storage.deleteRecord(this.uuids[counter]);

        delete this.uuids[counter];
        delete this.lines[counter];
    };

    this.getLineCount = counter => {
        const record = this.storage.getRecord(counter);

        if (record && record.lineCount) {
            return record.lineCount;
        }

        if (this.lines[counter]) {
            return this.lines[counter];
        }

        return 0;
    };

    this.pushFront = events => {
        const tail = this.getTailCounter();
        const newEvents = events.filter(({ counter }) => counter > tail);

        return this.storage.append(newEvents)
            .then(() => {
                newEvents.forEach(event => this.createRecord(event));

                return $q.resolve();
            });
    };

    this.pushBack = events => {
        const [head, tail] = this.getRange();
        const newEvents = events
            .filter(({ counter }) => counter < head || counter > tail);

        return this.storage.prepend(newEvents)
            .then(() => {
                newEvents.forEach(event => this.createRecord(event));

                return $q.resolve();
            });
    };

    this.popFront = count => {
        if (!count || count <= 0) {
            return $q.resolve();
        }

        const max = this.getTailCounter();
        const min = max - count;

        let lines = 0;

        for (let i = max; i >= min; --i) {
            lines += this.getLineCount(i);
        }

        return this.storage.pop(lines)
            .then(() => {
                for (let i = max; i >= min; --i) {
                    this.deleteRecord(i);
                    this.state.tail--;
                }

                return $q.resolve();
            });
    };

    this.popBack = count => {
        if (!count || count <= 0) {
            return $q.resolve();
        }

        const min = this.getHeadCounter();
        const max = min + count;

        let lines = 0;

        for (let i = min; i <= max; ++i) {
            lines += this.getLineCount(i);
        }

        return this.storage.shift(lines)
            .then(() => {
                for (let i = min; i <= max; ++i) {
                    this.deleteRecord(i);
                    this.state.head++;
                }

                return $q.resolve();
            });
    };

    this.clear = () => this.storage.clear()
        .then(() => {
            const [head, tail] = this.getRange();

            for (let i = head; i <= tail; ++i) {
                this.deleteRecord(i);
            }

            this.state.head = null;
            this.state.tail = null;

            return $q.resolve();
        });

    this.getNext = (displacement = OUTPUT_PAGE_SIZE) => {
        const next = this.getNextRange(displacement);
        const [head, tail] = this.getRange();

        this.chain = this.chain
            .then(() => this.api.getRange(next))
            .then(events => {
                const results = getContinuous(events);
                const min = Math.min(...results.map(({ counter }) => counter));

                if (min > tail + 1) {
                    return $q.resolve([]);
                }

                return $q.resolve(results);
            })
            .then(results => {
                const count = (tail - head + results.length);
                const excess = count - OUTPUT_EVENT_LIMIT;

                return this.popBack(excess)
                    .then(() => {
                        const popHeight = this.hooks.getScrollHeight();

                        return this.pushFront(results).then(() => $q.resolve(popHeight));
                    });
            });

        return this.chain;
    };

    this.getPrevious = (displacement = OUTPUT_PAGE_SIZE) => {
        const previous = this.getPreviousRange(displacement);
        const [head, tail] = this.getRange();

        this.chain = this.chain
            .then(() => this.api.getRange(previous))
            .then(events => {
                const results = getContinuous(events, true);
                const max = Math.max(...results.map(({ counter }) => counter));

                if (head > max + 1) {
                    return $q.resolve([]);
                }

                return $q.resolve(results);
            })
            .then(results => {
                const count = (tail - head + results.length);
                const excess = count - OUTPUT_EVENT_LIMIT;

                return this.popFront(excess)
                    .then(() => {
                        const popHeight = this.hooks.getScrollHeight();

                        return this.pushBack(results).then(() => $q.resolve(popHeight));
                    });
            });

        return this.chain;
    };

    this.getFirst = () => {
        this.chain = this.chain
            .then(() => this.clear())
            .then(() => {
                if (this.cache.first) {
                    return $q.resolve(this.cache.first);
                }

                return this.api.getFirst();
            })
            .then(events => {
                if (events.length === OUTPUT_PAGE_SIZE) {
                    this.cache.first = events;
                }

                return this.pushFront(events);
            });

        return this.chain
            .then(() => this.getNext());
    };

    this.getLast = () => {
        this.chain = this.chain
            .then(() => this.getFrames())
            .then(frames => {
                if (frames.length > 0) {
                    return $q.resolve(frames);
                }

                return this.api.getLast();
            })
            .then(events => {
                const min = Math.min(...events.map(({ counter }) => counter));

                if (min <= this.getTailCounter() + 1) {
                    return this.pushFront(events);
                }

                return this.clear()
                    .then(() => this.pushBack(events));
            });

        return this.chain
            .then(() => this.getPrevious());
    };

    this.getTailCounter = () => {
        if (this.state.tail === null) {
            return 0;
        }

        if (this.state.tail < 0) {
            return 0;
        }

        return this.state.tail;
    };

    this.getHeadCounter = () => {
        if (this.state.head === null) {
            return 0;
        }

        if (this.state.head < 0) {
            return 0;
        }

        return this.state.head;
    };

    this.pushFrames = events => {
        const frames = this.buffer.events.concat(events);
        const [head, tail] = this.getRange();

        let min;
        let max;
        let count = 0;

        for (let i = frames.length - 1; i >= 0; i--) {
            count++;

            if (count > API_MAX_PAGE_SIZE) {
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

    this.getRange = () => [this.getHeadCounter(), this.getTailCounter()];
    this.getRecordCount = () => Object.keys(this.lines).length;
    this.getCapacity = () => OUTPUT_EVENT_LIMIT - this.getRecordCount();
}

SlidingWindowService.$inject = ['$q'];

export default SlidingWindowService;
