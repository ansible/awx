/* eslint camelcase: 0 */
const PAGE_SIZE = 50;
const PAGE_LIMIT = 5;
const EVENT_LIMIT = PAGE_LIMIT * PAGE_SIZE;

const TAIL_ADDITION = 'TAIL_ADDITION';
const TAIL_DELETION = 'TAIL_DELETION';
const HEAD_ADDITION = 'HEAD_ADDITION';
const HEAD_DELETION = 'HEAD_DELETION';

function SlidingWindowService ($q) {
    this.init = (storage, api) => {
        const { prepend, append, shift, pop } = storage;
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
            pop
        };

        this.commands = {
            [TAIL_ADDITION]: this.pushFront,
            [HEAD_ADDITION]: this.pushBack,
            [TAIL_DELETION]: this.popFront,
            [HEAD_DELETION]: this.popBack
        };

        this.vectors = {
            [TAIL_ADDITION]: [0, 1],
            [HEAD_ADDITION]: [-1, 0],
            [TAIL_DELETION]: [0, -1],
            [HEAD_DELETION]: [1, 0],
        };

        this.records = {};
        this.chain = $q.resolve();
    };

    this.pushFront = events => {
        const tail = this.getTailCounter();
        const newEvents = events.filter(({ counter }) => counter > tail);

        return this.storage.append(newEvents)
            .then(() => {
                newEvents.forEach(({ counter, start_line, end_line }) => {
                    this.records[counter] = { start_line, end_line };
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
                newEvents.forEach(({ counter, start_line, end_line }) => {
                    this.records[counter] = { start_line, end_line };
                });

                return $q.resolve();
            });
    };

    this.popFront = count => {
        if (!count || count <= 0) {
            return $q.resolve();
        }

        const max = this.getTailCounter();
        const min = Math.max(this.getHeadCounter(), max - count);

        let lines = 0;

        for (let i = min; i <= max; ++i) {
            if (this.records[i]) {
                lines += (this.records[i].end_line - this.records[i].start_line);
            }
        }

        return this.storage.pop(lines)
            .then(() => {
                for (let i = min; i <= max; ++i) {
                    delete this.records[i];
                }

                return $q.resolve();
            });
    };

    this.popBack = count => {
        if (!count || count <= 0) {
            return $q.resolve();
        }

        const min = this.getHeadCounter();
        const max = Math.min(this.getTailCounter(), min + count);

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

        const additions = [];
        const deletions = [];

        for (let counter = tail + 1; counter <= newTail; counter++) {
            additions.push([counter, TAIL_ADDITION]);
        }

        for (let counter = head - 1; counter >= newHead; counter--) {
            additions.push([counter, HEAD_ADDITION]);
        }

        for (let counter = head; counter < newHead; counter++) {
            deletions.push([counter, HEAD_DELETION]);
        }

        for (let counter = tail; counter > newTail; counter--) {
            deletions.push([counter, TAIL_DELETION]);
        }

        const hasCounter = (items, n) => items
            .filter(([counter]) => counter === n).length !== 0;

        const commandRange = {
            [TAIL_DELETION]: 0,
            [HEAD_DELETION]: 0,
            [TAIL_ADDITION]: [tail, tail],
            [HEAD_ADDITION]: [head, head],
        };

        deletions.forEach(([counter, key]) => {
            if (!hasCounter(additions, counter)) {
                commandRange[key] += 1;
            }

            commandRange[TAIL_ADDITION][0] += this.vectors[key][0];
            commandRange[TAIL_ADDITION][1] += this.vectors[key][1];

            commandRange[HEAD_ADDITION][0] += this.vectors[key][0];
            commandRange[HEAD_ADDITION][1] += this.vectors[key][1];
        });

        additions.forEach(([counter, key]) => {
            if (!hasCounter(deletions, counter)) {
                if (counter < commandRange[key][0]) {
                    commandRange[key][0] = counter;
                }

                if (counter > commandRange[key][1]) {
                    commandRange[key][1] = counter;
                }
            }
        });

        this.chain = this.chain
            .then(() => this.commands[TAIL_DELETION](commandRange[TAIL_DELETION]))
            .then(() => this.commands[HEAD_DELETION](commandRange[HEAD_DELETION]))
            .then(() => this.api.getRange(commandRange[TAIL_ADDITION]))
            .then(events => this.commands[TAIL_ADDITION](events))
            .then(() => this.api.getRange(commandRange[HEAD_ADDITION]))
            .then(events => this.commands[HEAD_ADDITION](events))
            .then(() => {
                const range = this.getRange();
                const displacement = [range[0] - head, range[1] - tail];

                return $q.resolve(displacement);
            });

        return this.chain;
    };

    this.slideDown = (displacement = PAGE_SIZE) => {
        const [head, tail] = this.getRange();

        const tailRoom = this.getMaxCounter() - tail;
        const tailDisplacement = Math.min(tailRoom, displacement);
        const headDisplacement = Math.min(tailRoom, displacement);

        return this.move([head + headDisplacement, tail + tailDisplacement]);
    };

    this.slideUp = (displacement = PAGE_SIZE) => {
        const [head, tail] = this.getRange();

        const headRoom = head - 1;
        const headDisplacement = Math.min(headRoom, displacement);
        const tailDisplacement = Math.min(headRoom, displacement);

        return this.move([head - headDisplacement, tail - tailDisplacement]);
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
                .then(() => this.commands[HEAD_DELETION](count));
        }

        return this.chain;
    };

    this.getFirst = () => this.clear()
        .then(() => this.api.getFirst())
        .then(events => this.commands[TAIL_ADDITION](events))
        .then(() => this.moveTail(PAGE_SIZE));

    this.getLast = () => this.clear()
        .then(() => this.api.getLast())
        .then(events => this.commands[HEAD_ADDITION](events))
        .then(() => this.moveHead(-PAGE_SIZE));

    this.getTailCounter = () => {
        const tail = Math.max(...Object.keys(this.records));

        return Number.isFinite(tail) ? tail : 0;
    };

    this.getHeadCounter = () => {
        const head = Math.min(...Object.keys(this.records));

        return Number.isFinite(head) ? head : 0;
    };

    this.compareRange = (a, b) => a[0] === b[0] && a[1] === b[1];
    this.getRange = () => [this.getHeadCounter(), this.getTailCounter()];

    this.getMaxCounter = () => this.api.getMaxCounter();
    this.getRecordCount = () => Object.keys(this.records).length;
    this.getCapacity = () => EVENT_LIMIT - this.getRecordCount();
}

SlidingWindowService.$inject = ['$q'];

export default SlidingWindowService;
