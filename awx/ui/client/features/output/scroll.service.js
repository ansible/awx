const ELEMENT_CONTAINER = '.at-Stdout-container';
const ELEMENT_TBODY = '#atStdoutResultTable';
const DELAY = 100;
const THRESHOLD = 0.1;

function JobScrollService ($q, $timeout) {
    this.init = ({ next, previous }) => {
        this.el = $(ELEMENT_CONTAINER);
        this.timer = null;

        this.position = {
            previous: 0,
            current: 0
        };

        this.hooks = {
            next,
            previous,
            isAtRest: () => $q.resolve()
        };

        this.state = {
            hidden: false,
            paused: false,
            top: true,
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
        const height = this.getScrollHeight();

        if (downward) {
            current += this.getViewableHeight();

            if (current >= height || ((height - current) / height) < THRESHOLD) {
                return true;
            }
        } else if (current <= 0 || (current / height) < THRESHOLD) {
            return true;
        }

        return false;
    };

    /**
     * Move scroll position up by one page of visible content.
     */
    this.moveUp = () => {
        const top = this.getScrollPosition();
        const height = this.getViewableHeight();

        this.setScrollPosition(top - height);
    };

    /**
     * Move scroll position down by one page of visible content.
     */
    this.moveDown = () => {
        const top = this.getScrollPosition();
        const height = this.getViewableHeight();

        this.setScrollPosition(top + height);
    };

    this.getScrollHeight = () => this.el[0].scrollHeight;
    this.getViewableHeight = () => this.el[0].offsetHeight;

    /**
     * Get the vertical scroll position.
     *
     * @returns {Number} - The number of pixels that are hidden from view above the scrollable area.
     */
    this.getScrollPosition = () => this.el[0].scrollTop;

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

    this.isPaused = () => this.state.paused;

    this.lock = () => {
        this.state.locked = true;
    };

    this.unlock = () => {
        this.state.locked = false;
    };

    this.hide = () => {
        if (!this.state.hidden) {
            this.el.css('overflow', 'hidden');
            this.state.hidden = true;
        }
    };

    this.unhide = () => {
        if (this.state.hidden) {
            this.el.css('overflow', 'auto');
            this.state.hidden = false;
        }
    };

    this.isLocked = () => this.state.locked;
    this.isMissing = () => $(ELEMENT_TBODY)[0].clientHeight < this.getViewableHeight();
}

JobScrollService.$inject = ['$q', '$timeout'];

export default JobScrollService;
