const ELEMENT_CONTAINER = '.at-Stdout-container';
const DELAY = 100;
const THRESHOLD = 0.1;

function JobScrollService ($q, $timeout) {
    this.init = (hooks) => {
        this.el = $(ELEMENT_CONTAINER);
        this.timer = null;

        this.position = {
            previous: 0,
            current: 0
        };

        this.hooks = {
            isAtRest: hooks.isAtRest,
            next: hooks.next,
            previous: hooks.previous
        };

        this.state = {
            locked: false,
            paused: false,
            top: true
        };

        this.el.scroll(this.listen);
    };

    this.listen = () => {
        if (this.isPaused()) {
            return;
        }

        if (this.timer) {
            $timeout.cancel(this.timer);
        }

        this.timer = $timeout(this.register, DELAY);
    };

    this.register = () => {
        this.pause();

        const height = this.getScrollHeight();
        const current = this.getScrollPosition();
        const downward = current > this.position.previous;

        let promise;

        if (downward && this.isBeyondThreshold(downward, current)) {
            promise = this.hooks.next;
        } else if (!downward && this.isBeyondThreshold(downward, current)) {
            promise = this.hooks.previous;
        }

        if (!promise) {
            this.setScrollPosition(current);
            this.isAtRest();
            this.resume();

            return $q.resolve();
        }

        return promise()
            .then(() => {
                this.setScrollPosition(this.getScrollPosition());
                this.isAtRest();
                this.resume();
            });
    };

    this.isBeyondThreshold = (downward, current) => {
         const previous = this.position.previous;
         const height = this.getScrollHeight();

         if (downward) {
            current += this.getViewableHeight();

            if (current >= height || ((height - current) / height) < THRESHOLD) {
                return true;
            }
        } else {
            if (current <= 0 || (current / height) < THRESHOLD) {
                return true;
            }
        }

        return false;
    };

    this.pageUp = () => {
        if (this.isPaused()) {
            return;
        }

        const top = this.getScrollPosition();
        const height = this.getViewableHeight();

        this.setScrollPosition(top - height);
    };

    this.pageDown = () => {
        if (this.isPaused()) {
            return;
        }

        const top = this.getScrollPosition();
        const height = this.getViewableHeight();

        this.setScrollPosition(top + height);
    };

    this.getScrollHeight = () => {
        return this.el[0].scrollHeight;
    };

    this.getViewableHeight = () => {
        return this.el[0].offsetHeight;
    };

    this.getScrollPosition = () => {
        return this.el[0].scrollTop;
    };

    this.setScrollPosition = position => {
        this.position.previous = this.position.current;
        this.position.current = position;
        this.el[0].scrollTop = position;
        this.isAtRest();
    };

    this.resetScrollPosition = () => {
        this.position.previous = 0;
        this.position.current = 0;
        this.el[0].scrollTop = 0;
        this.isAtRest();
    };

    this.scrollToBottom = () => {
        this.setScrollPosition(this.getScrollHeight());
    };

    this.isAtRest = () => {
        if (this.position.current === 0 && !this.state.top) {
            this.state.top = true;
            this.hooks.isAtRest(true);
        } else if (this.position.current > 0 && this.state.top) {
            this.state.top = false;
            this.hooks.isAtRest(false);
        }
    };

    this.resume = () => {
        this.state.paused = false;
    };

    this.pause = () => {
        this.state.paused = true;
    };

    this.isPaused = () => {
        return this.state.paused;
    };

    this.lock = () => {
        this.state.locked = true;
    };

    this.unlock = () => {
        this.state.locked = false;
    };

    this.isLocked = () => {
        return this.state.locked;
    };
}

JobScrollService.$inject = ['$q', '$timeout'];

export default JobScrollService;
