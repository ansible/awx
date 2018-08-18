/* eslint camelcase: 0 */
import {
    EVENT_STATS_PLAY,
    OUTPUT_MAX_LAG,
    OUTPUT_PAGE_SIZE,
} from './constants';

const rx = [];

function OutputStream ($q) {
    this.init = ({ onFrames, onFrameRate, onStop }) => {
        this.hooks = {
            onFrames,
            onFrameRate,
            onStop,
        };

        this.state = {
            ending: false,
            ended: false,
        };

        this.lag = 0;
        this.chain = $q.resolve();
        this.factors = this.calcFactors(OUTPUT_PAGE_SIZE);

        this.setFramesPerRender();
        this.bufferInit();
    };

    this.bufferInit = () => {
        rx.length = 0;

        this.counters = {
            total: 0,
            min: 0,
            max: null,
            final: null,
            ready: [],
            used: [],
            missing: [],
        };
    };

    this.bufferEmpty = (minReady, maxReady) => {
        let removed = [];

        for (let i = rx.length - 1; i >= 0; i--) {
            if (rx[i].counter <= maxReady) {
                removed = removed.concat(rx.splice(i, 1));
            }
        }

        return removed;
    };

    this.bufferAdd = event => {
        rx.push(event);

        this.counters.total += 1;

        return this.counters.total;
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
        const index = Math.floor((this.lag / OUTPUT_MAX_LAG) * this.factors.length);
        const boundedIndex = Math.min(this.factors.length - 1, index);

        this.framesPerRender = this.factors[boundedIndex];
        this.hooks.onFrameRate(this.framesPerRender);
    };

    this.setMissingCounterThreshold = counter => {
        if (counter > this.counters.min) {
            this.counters.min = counter;
        }
    };

    this.checkCounter = ({ counter }) => {
        this.counters.used.push(counter);

        if (!this.counters.max || this.counters.max < counter) {
            this.counters.max = counter;
        }

        let ready;
        const missing = [];

        for (let i = this.counters.min; i <= this.counters.max; i++) {
            if (this.counters.used.indexOf(i) === -1) {
                missing.push(i);
            }
        }

        if (missing.length === 0) {
            ready = this.counters.max;
        } else {
            ready = missing[0] - 1;
        }

        this.counters.ready = [this.counters.min, ready];
        this.counters.min = ready + 1;
        this.counters.used = this.counters.used.filter(c => c > ready);
        this.counters.missing = missing;

        return this.counters.ready;
    };

    this.pushJobEvent = data => {
        this.lag++;

        this.chain = this.chain
            .then(() => {
                if (data.event === EVENT_STATS_PLAY) {
                    this.state.ending = true;
                    this.counters.final = data.counter;
                }

                const [minReady, maxReady] = this.checkCounter(data);
                const count = this.bufferAdd(data);

                if (count % OUTPUT_PAGE_SIZE === 0) {
                    this.setFramesPerRender();
                }

                const isReady = maxReady && (this.state.ending ||
                    count % this.framesPerRender === 0 ||
                    count < OUTPUT_PAGE_SIZE && (maxReady - minReady) % this.framesPerRender === 0);

                if (!isReady) {
                    return $q.resolve();
                }

                const isLastFrame = this.state.ending && (maxReady >= this.counters.final);
                const events = this.bufferEmpty(minReady, maxReady);

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
                    events = this.bufferEmpty(...this.counters.ready);
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

    this.getMaxCounter = () => this.counters.max;
}

OutputStream.$inject = ['$q'];

export default OutputStream;
