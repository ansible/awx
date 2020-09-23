/* eslint camelcase: 0 */
import {
    EVENT_STATS_PLAY,
    OUTPUT_MAX_BUFFER_LENGTH,
    OUTPUT_MAX_LAG,
    OUTPUT_PAGE_SIZE,
    OUTPUT_EVENT_LIMIT,
} from './constants';

const rx = [];

function OutputStream ($q) {
    this.init = ({ onFrames, onFrameRate, onStop }) => {
        this.hooks = {
            onFrames,
            onFrameRate,
            onStop,
        };

        this.bufferInit();
    };

    this.bufferInit = () => {
        rx.length = 0;

        this.counters = {
            min: 1,
            max: -1,
            ready: -1,
            final: null,
            used: [],
            missing: [],
            total: 0,
            length: 0,
        };

        this.state = {
            ending: false,
            ended: false,
            overflow: false,
        };

        this.lag = 0;
        this.chain = $q.resolve();

        this.factors = this.calcFactors(OUTPUT_EVENT_LIMIT);
        this.setFramesPerRender();
    };

    this.calcFactors = size => {
        const factors = [1];

        if (size !== parseInt(size, 10) || size <= 1) {
            return factors;
        }

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

    this.bufferAdd = event => {
        const { counter } = event;

        if (counter > this.counters.max) {
            this.counters.max = counter;
        }

        let ready;
        const used = [];
        const missing = [];

        for (let i = this.counters.min; i <= this.counters.max; i++) {
            if (this.counters.used.indexOf(i) === -1) {
                if (i === counter) {
                    rx.push(event);
                    used.push(i);
                    this.counters.length += 1;
                } else {
                    missing.push(i);
                }
            } else {
                used.push(i);
            }
        }

        const excess = this.counters.length - OUTPUT_MAX_BUFFER_LENGTH;
        this.state.overflow = (excess > 0);

        if (missing.length === 0) {
            ready = this.counters.max;
        } else if (this.state.overflow) {
            ready = this.counters.min + this.framesPerRender;
        } else {
            ready = missing[0] - 1;
        }

        this.counters.total += 1;
        this.counters.ready = ready;
        this.counters.used = used;
        this.counters.missing = missing;

        if (!window.liveUpdates) {
            this.counters.ready = event.counter;
        }
    };

    this.bufferEmpty = threshold => {
        let removed = [];

        for (let i = rx.length - 1; i >= 0; i--) {
            if (rx[i].counter <= threshold) {
                removed = removed.concat(rx.splice(i, 1));
            }
        }

        this.counters.min = threshold + 1;
        this.counters.used = this.counters.used.filter(c => c > threshold);
        this.counters.length = rx.length;

        return removed;
    };

    this.isReadyToRender = () => {
        const { total } = this.counters;
        const readyCount = this.getReadyCount();

        if (!window.liveUpdates) {
            return true;
        }

        if (readyCount <= 0) {
            return false;
        }

        if (this.state.ending) {
            return true;
        }

        if (total % this.framesPerRender === 0) {
            return true;
        }

        if (total < OUTPUT_PAGE_SIZE) {
            if (readyCount % this.framesPerRender === 0) {
                return true;
            }
        }

        return false;
    };

    this.pushJobEvent = data => {
        this.lag++;

        this.chain = this.chain
            .then(() => {
                if (data.event === EVENT_STATS_PLAY) {
                    this.state.ending = true;
                    this.counters.final = data.counter;
                }

                this.bufferAdd(data);

                if (this.counters.total % OUTPUT_PAGE_SIZE === 0) {
                    this.setFramesPerRender();
                }

                if (!this.isReadyToRender()) {
                    return $q.resolve();
                }

                const isLast = this.state.ending && (this.counters.ready >= this.counters.final);
                const events = this.bufferEmpty(this.counters.ready);

                if (events.length > 0) {
                    return this.emitFrames(events, isLast);
                }

                return $q.resolve();
            })
            .then(() => --this.lag);

        return this.chain;
    };

    this.setFinalCounter = counter => {
        this.chain = this.chain
            .then(() => {
                this.state.ending = true;
                this.counters.final = counter;

                if (counter > this.counters.ready) {
                    return $q.resolve();
                }

                const readyCount = this.getReadyCount();

                let events = [];
                if (readyCount > 0) {
                    events = this.bufferEmpty(this.counters.ready);

                    return this.emitFrames(events, true);
                }

                return $q.resolve();
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

            return $q.resolve();
        });

    this.getMaxCounter = () => this.counters.max;
    this.getReadyCount = () => this.counters.ready - this.counters.min + 1;
}

OutputStream.$inject = ['$q'];

export default OutputStream;
