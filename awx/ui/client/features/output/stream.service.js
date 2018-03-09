const JOB_START = 'playbook_on_start';
const JOB_END = 'playbook_on_stats';
const MAX_LAG = 120;

function JobStreamService ($q) {
    this.init = ({ resource, scroll, page, render, listen }) => {
        this.resource = resource;
        this.scroll = scroll;
        this.page = page;

        this.lag = 0;
        this.count = 0;
        this.pageCount = 0;
        this.chain = $q.resolve();
        this.factors = this.getBatchFactors(this.resource.page.size);
        this.state = {
            started: false,
            paused: false,
            pausing: false,
            resuming: false,
            ending: false,
            ended: false
        };

        this.hooks = {
            render,
            listen
        };

        this.hooks.listen(resource.ws.namespace, this.listen);
    };

    this.getBatchFactors = size => {
        const factors = [1];

        for (let i = 2; i <= size / 2; i++) {
            if (size % i === 0) {
                factors.push(i);
            }
        }

        factors.push(size);

        return factors;
    };

    this.getBatchFactorIndex = () => {
        const index = Math.floor((this.lag / MAX_LAG) * this.factors.length);

        return index > this.factors.length - 1 ? this.factors.length - 1 : index;
    };

    this.setBatchFrameCount = () => {
        const index = this.getBatchFactorIndex();

        this.framesPerRender = this.factors[index];
    };

    this.buffer = data => {
        const pageAdded = this.page.addToBuffer(data);

        this.pageCount++;

        if (pageAdded) {
            this.setBatchFrameCount();

            if (this.isPausing()) {
                this.pause(true);
            } else if (this.isResuming()) {
                this.resume(true);
            }
        }
    };

    this.listen = data => {
        this.lag++;

        this.chain = this.chain
            .then(() => {
                if (data.event === JOB_START) {
                    this.start();
                } else if (data.event === JOB_END) {
                    if (this.isPaused()) {
                        this.end(true);
                    } else {
                        this.end();
                    }
                }

                this.buffer(data);
                this.count++;

                if (this.isPaused() || !this.isBatchFull()) {
                    return $q.resolve();
                }

                const events = this.page.emptyBuffer();
                this.count -= events.length;

                return this.renderFrame(events);
            })
            .then(() => --this.lag);
    };

    this.renderFrame = events => this.hooks.render(events)
        .then(() => {
            if (this.scroll.isLocked()) {
                this.scroll.scrollToBottom();
            }

            if (this.isEnding()) {
                const lastEvents = this.page.emptyBuffer();

                if (lastEvents.length) {
                    return this.renderFrame(lastEvents);
                }

                this.end(true);
            }

            return $q.resolve();
        });

    this.resume = done => {
        if (done) {
            this.state.resuming = false;
            this.state.paused = false;
        } else if (!this.isTransitioning()) {
            this.scroll.pause();
            this.scroll.lock();
            this.scroll.scrollToBottom();
            this.state.resuming = true;
            this.page.removeBookmark();
        }
    };

    this.pause = done => {
        if (done) {
            this.state.pausing = false;
            this.state.paused = true;
            this.scroll.resume();
        } else if (!this.isTransitioning()) {
            this.scroll.pause();
            this.scroll.unlock();
            this.state.pausing = true;
            this.page.setBookmark();
        }
    };

    this.start = () => {
        this.state.started = true;
        this.scroll.pause();
        this.scroll.lock();
    };

    this.end = done => {
        if (done) {
            this.state.ending = false;
            this.state.ended = true;
            this.scroll.unlock();
            this.scroll.resume();

            return;
        }

        this.state.ending = true;
    };

    this.isBatchFull = () => this.count % this.framesPerRender === 0;
    this.isPaused = () => this.state.paused;
    this.isPausing = () => this.state.pausing;
    this.isResuming = () => this.state.resuming;
    this.isTransitioning = () => this.isActive() && (this.state.pausing || this.state.resuming);
    this.isActive = () => this.state.started && !this.state.ended;
    this.isEnding = () => this.state.ending;
    this.isDone = () => this.state.ended;
}

JobStreamService.$inject = ['$q'];

export default JobStreamService;
