/* eslint camelcase: 0 */
const PAGE_SIZE = 50;
const MAX_LAG = 120;
const JOB_END = 'playbook_on_stats';

function OutputStream ($q) {
    this.init = ({ bufferAdd, bufferEmpty, onFrames, onStop }) => {
        this.hooks = {
            bufferAdd,
            bufferEmpty,
            onFrames,
            onStop,
        };

        this.counters = {
            used: [],
            min: 1,
            max: 0,
            ready: false,
        };

        this.state = {
            ending: false,
            ended: false
        };

        this.lag = 0;
        this.chain = $q.resolve();

        this.factors = this.calcFactors(PAGE_SIZE);
        this.setFramesPerRender();
    };

    this.calcFactors = size => {
        const factors = [1];

        for (let i = 2; i <= size / 2; i++) {
            if (size % i === 0) {
                factors.push(i);
            }
        }

        factors.push(size);

        return factors;
    };

    this.setFramesPerRender = () => {
        const index = Math.floor((this.lag / MAX_LAG) * this.factors.length);
        const boundedIndex = Math.min(this.factors.length - 1, index);

        this.framesPerRender = this.factors[boundedIndex];
    };

    this.setMissingCounterThreshold = counter => {
        if (counter > this.counters.min) {
            this.counters.min = counter;
        }
    };

    this.updateCounterState = ({ counter }) => {
        this.counters.used.push(counter);

        if (counter > this.counters.max) {
            this.counters.max = counter;
        }

        const missing = [];
        const ready = [];

        for (let i = this.counters.min; i < this.counters.max; i++) {
            if (this.counters.used.indexOf(i) === -1) {
                missing.push(i);
            } else if (missing.length === 0) {
                ready.push(i);
            }
        }

        if (missing.length === 0) {
            this.counters.ready = true;
            this.counters.min = this.counters.max + 1;
            this.counters.used = [];
        } else {
            this.counters.ready = false;
        }

        this.counters.missing = missing;
        this.counters.readyLines = ready;

        return this.counters.ready;
    };

    this.pushJobEvent = data => {
        this.lag++;

        this.chain = this.chain
            .then(() => {
                if (data.event === JOB_END) {
                    this.state.ending = true;
                }

                const isMissingCounters = !this.updateCounterState(data);
                const [length, count] = this.hooks.bufferAdd(data);

                if (count % PAGE_SIZE === 0) {
                    this.setFramesPerRender();
                }

                const isBatchReady = length % this.framesPerRender === 0;
                const isReady = this.state.ended || (!isMissingCounters && isBatchReady);

                if (!isReady) {
                    return $q.resolve();
                }

                const events = this.hooks.bufferEmpty();

                return this.emitFrames(events);
            })
            .then(() => --this.lag);

        return this.chain;
    };

    this.emitFrames = events => this.hooks.onFrames(events)
        .then(() => {
            if (this.state.ending) {
                const lastEvents = this.hooks.bufferEmpty();

                if (lastEvents.length) {
                    return this.emitFrames(lastEvents);
                }

                this.state.ending = false;
                this.state.ended = true;

                this.hooks.onStop();
            }

            return $q.resolve();
        });
}

OutputStream.$inject = ['$q'];

export default OutputStream;
