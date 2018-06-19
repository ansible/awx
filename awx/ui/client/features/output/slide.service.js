/* eslint camelcase: 0 */
const PAGE_SIZE = 50;
const PAGE_LIMIT = 5;
const EVENT_LIMIT = PAGE_LIMIT * PAGE_SIZE;

/**
 * Check if a range overlaps another range
 *
 * @arg {Array} range - A [low, high] range array.
 * @arg {Array} other - A [low, high] range array to be compared with the first.
 *
 * @returns {Boolean} - Indicating that the ranges overlap.
 */
function checkRangeOverlap (range, other) {
    const span = Math.max(range[1], other[1]) - Math.min(range[0], other[0]);

    return (range[1] - range[0]) + (other[1] - other[0]) >= span;
}

/**
 * Get an array that describes the overlap of two ranges.
 *
 * @arg {Array} range - A [low, high] range array.
 * @arg {Array} other - A [low, high] range array to be compared with the first.
 *
 * @returns {(Array|Boolean)} - Returns false if the ranges aren't overlapping.
 * For overlapping ranges, a length-2 array describing the nature of the overlap
 * is returned. The overlap array describes the position of the second range in
 * terms of how many steps inward (negative) or outward (positive) its sides are
 * relative to the first range.
 *
 *  ++45678
 *  234---- => getOverlapArray([4, 8], [2, 4]) = [2, -4]
 *
 *  45678
 *  45---   => getOverlapArray([4, 8], [4, 5]) = [0, -3]
 *
 *  45678
 *  -56--   => getOverlapArray([4, 8], [5, 6]) = [-1, -2]
 *
 *  45678
 *  --678   => getOverlapArray([4, 8], [6, 8]) = [-2, 0]
 *
 *  456++
 *  --678   => getOverlapArray([4, 6], [6, 8]) = [-2, 2]
 *
 * +++456++
 * 12345678 => getOverlapArray([4, 6], [1, 8]) = [3, 2]
 ^
 * 12345678
 * ---456-- => getOverlapArray([1, 8], [4, 6]) = [-3, -2]
 */
function getOverlapArray (range, other) {
    if (!checkRangeOverlap(range, other)) {
        return false;
    }

    return [range[0] - other[0], other[1] - range[1]];
}

function SlidingWindowService ($q) {
    this.init = (storage, api, { getScrollHeight }) => {
        const { prepend, append, shift, pop, deleteRecord } = storage;
        const { getMaxCounter, getRange, getFirst, getLast } = api;

        this.api = {
            getMaxCounter,
            getRange,
            getFirst,
            getLast
        };

        this.storage = {
            prepend,
            append,
            shift,
            pop,
            deleteRecord,
        };

        this.hooks = {
            getScrollHeight,
        };

        this.records = {};
        this.uuids = {};
        this.chain = $q.resolve();
    };

    this.pushFront = events => {
        const tail = this.getTailCounter();
        const newEvents = events.filter(({ counter }) => counter > tail);

        return this.storage.append(newEvents)
            .then(() => {
                newEvents.forEach(({ counter, start_line, end_line, uuid }) => {
                    this.records[counter] = { start_line, end_line };
                    this.uuids[counter] = uuid;
                });

                return $q.resolve();
            });
    };

    this.pushBack = events => {
        const [head, tail] = this.getRange();
        const newEvents = events
            .filter(({ counter }) => counter < head || counter > tail);

        return this.storage.prepend(newEvents)
            .then(() => {
                newEvents.forEach(({ counter, start_line, end_line, uuid }) => {
                    this.records[counter] = { start_line, end_line };
                    this.uuids[counter] = uuid;
                });

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
            if (this.records[i]) {
                lines += (this.records[i].end_line - this.records[i].start_line);
            }
        }

        return this.storage.pop(lines)
            .then(() => {
                for (let i = max; i >= min; --i) {
                    delete this.records[i];

                    this.storage.deleteRecord(this.uuids[i]);
                    delete this.uuids[i];
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
            if (this.records[i]) {
                lines += (this.records[i].end_line - this.records[i].start_line);
            }
        }

        return this.storage.shift(lines)
            .then(() => {
                for (let i = min; i <= max; ++i) {
                    delete this.records[i];

                    this.storage.deleteRecord(this.uuids[i]);
                    delete this.uuids[i];
                }

                return $q.resolve();
            });
    };

    this.getBoundedRange = ([low, high]) => {
        const bounds = [1, this.getMaxCounter()];

        return [Math.max(low, bounds[0]), Math.min(high, bounds[1])];
    };

    this.move = ([low, high]) => {
        const [head, tail] = this.getRange();
        const [newHead, newTail] = this.getBoundedRange([low, high]);

        if (newHead > newTail) {
            return $q.resolve([0, 0]);
        }

        if (!Number.isFinite(newHead) || !Number.isFinite(newTail)) {
            return $q.resolve([0, 0]);
        }

        const overlap = getOverlapArray([head, tail], [newHead, newTail]);

        if (!overlap) {
            this.chain = this.chain
                .then(() => this.popBack(this.getRecordCount()))
                .then(() => this.api.getRange([newHead, newTail]))
                .then(events => this.pushFront(events));
        }

        if (overlap && overlap[0] < 0) {
            this.chain = this.chain.then(() => this.popBack(Math.abs(overlap[0])));
        }

        if (overlap && overlap[1] < 0) {
            this.chain = this.chain.then(() => this.popFront(Math.abs(overlap[1])));
        }

        let popHeight;
        this.chain = this.chain.then(() => {
            popHeight = this.hooks.getScrollHeight();

            return $q.resolve();
        });

        if (overlap && overlap[0] > 0) {
            const pushBackRange = [head - overlap[0], head];

            this.chain = this.chain
                .then(() => this.api.getRange(pushBackRange))
                .then(events => this.pushBack(events));
        }

        if (overlap && overlap[1] > 0) {
            const pushFrontRange = [tail, tail + overlap[1]];

            this.chain = this.chain
                .then(() => this.api.getRange(pushFrontRange))
                .then(events => this.pushFront(events));
        }

        this.chain = this.chain
            .then(() => $q.resolve(popHeight));

        return this.chain;
    };

    this.slideDown = (displacement = PAGE_SIZE) => {
        const [head, tail] = this.getRange();

        const tailRoom = this.getMaxCounter() - tail;
        const tailDisplacement = Math.min(tailRoom, displacement);

        const newTail = tail + tailDisplacement;

        let headDisplacement = 0;

        if (newTail - head > EVENT_LIMIT) {
            headDisplacement = (newTail - EVENT_LIMIT) - head;
        }

        return this.move([head + headDisplacement, tail + tailDisplacement]);
    };

    this.slideUp = (displacement = PAGE_SIZE) => {
        const [head, tail] = this.getRange();

        const headRoom = head - 1;
        const headDisplacement = Math.min(headRoom, displacement);

        const newHead = head - headDisplacement;

        let tailDisplacement = 0;

        if (tail - newHead > EVENT_LIMIT) {
            tailDisplacement = tail - (newHead + EVENT_LIMIT);
        }

        return this.move([newHead, tail - tailDisplacement]);
    };

    this.moveHead = displacement => {
        const [head, tail] = this.getRange();

        const headRoom = head - 1;
        const headDisplacement = Math.min(headRoom, displacement);

        return this.move([head + headDisplacement, tail]);
    };

    this.moveTail = displacement => {
        const [head, tail] = this.getRange();

        const tailRoom = this.getMaxCounter() - tail;
        const tailDisplacement = Math.max(tailRoom, displacement);

        return this.move([head, tail + tailDisplacement]);
    };

    this.clear = () => {
        const count = this.getRecordCount();

        if (count > 0) {
            this.chain = this.chain
                .then(() => this.popBack(count));
        }

        return this.chain;
    };

    this.getFirst = () => this.clear()
        .then(() => this.api.getFirst())
        .then(events => this.pushFront(events))
        .then(() => this.moveTail(PAGE_SIZE));

    this.getLast = () => this.clear()
        .then(() => this.api.getLast())
        .then(events => this.pushBack(events))
        .then(() => this.moveHead(-PAGE_SIZE));

    this.getTailCounter = () => {
        const tail = Math.max(...Object.keys(this.records));

        return Number.isFinite(tail) ? tail : 0;
    };

    this.getHeadCounter = () => {
        const head = Math.min(...Object.keys(this.records));

        return Number.isFinite(head) ? head : 0;
    };

    this.getMaxCounter = () => {
        const counter = this.api.getMaxCounter();
        const tail = this.getTailCounter();

        return Number.isFinite(counter) ? Math.max(tail, counter) : tail;
    };

    this.getRange = () => [this.getHeadCounter(), this.getTailCounter()];
    this.getRecordCount = () => Object.keys(this.records).length;
    this.getCapacity = () => EVENT_LIMIT - this.getRecordCount();
}

SlidingWindowService.$inject = ['$q'];

export default SlidingWindowService;
