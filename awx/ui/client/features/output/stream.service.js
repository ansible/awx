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
            ready: [],
            min: 1,
            max: 0,
            final: null,
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
        let minReady;
        let maxReady;

        for (let i = this.counters.min; i <= this.counters.max; i++) {
            if (this.counters.used.indexOf(i) === -1) {
                missing.push(i);
            } else if (missing.length === 0) {
                maxReady = i;
            }
        }

        if (maxReady) {
            minReady = this.counters.min;

            this.counters.min = maxReady + 1;
            this.counters.used = this.counters.used.filter(c => c > maxReady);
        }

        this.counters.missing = missing;
        this.counters.ready = [minReady, maxReady];

        return this.counters.ready;
    };

    this.pushJobEvent = data => {
        this.lag++;

        this.chain = this.chain
            .then(() => {
                if (data.event === JOB_END) {
                    this.state.ending = true;
                    this.counters.final = data.counter;
                }

                const [minReady, maxReady] = this.updateCounterState(data);
                const count = this.hooks.bufferAdd(data);

                if (count % PAGE_SIZE === 0) {
                    this.setFramesPerRender();
                }

                const isReady = maxReady && (this.state.ending ||
                    (maxReady - minReady) % this.framesPerRender === 0);

                if (!isReady) {
                    return $q.resolve();
                }

                const isLastFrame = this.state.ending && (maxReady >= this.counters.final);
                const events = this.hooks.bufferEmpty(minReady, maxReady);

                return this.emitFrames(events, isLastFrame);
            })
            .then(() => --this.lag);

        return this.chain;
    };

    this.setFinalCounter = counter => {
        this.chain = this.chain
            .then(() => {
                this.state.ending = true;
                this.counters.final = counter;

                if (counter >= this.counters.min) {
                    return $q.resolve();
                }

                let events = [];
                if (this.counters.ready.length > 0) {
                    events = this.hooks.bufferEmpty(...this.counters.ready);
                }

                return this.emitFrames(events, true);
            });

        return this.chain;
    };

    this.emitFrames = (events, last) => this.hooks.onFrames(events)
        .then(() => {
            if (last) {
                this.state.ending = false;
                this.state.ended = true;

                this.hooks.onStop();
            }

            this.counters.ready.length = 0;
            return $q.resolve();
        });
}

OutputStream.$inject = ['$q'];

export default OutputStream;
