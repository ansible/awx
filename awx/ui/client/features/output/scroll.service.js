import {
    OUTPUT_ELEMENT_CONTAINER,
    OUTPUT_ELEMENT_TBODY,
    OUTPUT_SCROLL_DELAY,
    OUTPUT_SCROLL_THRESHOLD,
} from './constants';

function JobScrollService ($q, $timeout) {
    this.init = ({ next, previous, onThresholdLeave }) => {
        this.el = $(OUTPUT_ELEMENT_CONTAINER);
        this.chain = $q.resolve();
        this.timer = null;

        this.position = {
            previous: 0,
            current: 0
        };

        this.threshold = {
            previous: 0,
            current: 0,
        };

        this.hooks = {
            next,
            previous,
            onThresholdLeave,
        };

        this.state = {
            paused: false,
            locked: false,
            hover: false,
            thrash: 0,
        };

        this.el.scroll(this.listen);
        this.el.mouseenter(this.onMouseEnter);
        this.el.mouseleave(this.onMouseLeave);
    };

    this.onMouseEnter = () => {
        this.state.hover = true;
    };

    this.onMouseLeave = () => {
        this.state.hover = false;
    };

    this.listen = () => {
        if (this.isPaused()) {
            return;
        }

        if (this.isLocked()) {
            return;
        }

        if (!this.state.hover) {
            return;
        }

        if (this.timer) {
            $timeout.cancel(this.timer);
        }

        this.timer = $timeout(this.register, OUTPUT_SCROLL_DELAY);
    };

    this.register = () => {
        const position = this.getScrollPosition();
        const viewport = this.getScrollHeight() - this.getViewableHeight();

        const threshold = position / viewport;
        const downward = position > this.position.previous;

        const isBeyondUpperThreshold = threshold < OUTPUT_SCROLL_THRESHOLD;
        const isBeyondLowerThreshold = (1 - threshold) < OUTPUT_SCROLL_THRESHOLD;

        const wasBeyondUpperThreshold = this.threshold.previous < OUTPUT_SCROLL_THRESHOLD;
        const wasBeyondLowerThreshold = (1 - this.threshold.previous) < OUTPUT_SCROLL_THRESHOLD;

        const enteredUpperThreshold = isBeyondUpperThreshold && !wasBeyondUpperThreshold;
        const enteredLowerThreshold = isBeyondLowerThreshold && !wasBeyondLowerThreshold;
        const leftLowerThreshold = !isBeyondLowerThreshold && wasBeyondLowerThreshold;

        const transitions = [];

        if (position <= 0 || enteredUpperThreshold) {
            transitions.push(this.hooks.onThresholdLeave);
            transitions.push(this.hooks.previous);
        }

        if (leftLowerThreshold) {
            transitions.push(this.hooks.onThresholdLeave);
        }

        if (threshold >= 1 || enteredLowerThreshold) {
            transitions.push(this.hooks.next);
        }

        if (!downward) {
            transitions.reverse();
        }

        this.position.current = position;
        this.threshold.current = threshold;

        transitions.forEach(promise => {
            this.chain = this.chain.then(() => promise());
        });

        return this.chain
            .then(() => {
                this.setScrollPosition(this.getScrollPosition());

                return $q.resolve();
            });
    };

    /**
     * Move scroll position up by one page of visible content.
     */
    this.moveUp = () => {
        const position = this.getScrollPosition() - this.getViewableHeight();

        this.setScrollPosition(position);
    };

    /**
     * Move scroll position down by one page of visible content.
     */
    this.moveDown = () => {
        const position = this.getScrollPosition() + this.getViewableHeight();

        this.setScrollPosition(position);
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
        const viewport = this.getScrollHeight() - this.getViewableHeight();

        this.position.previous = this.position.current;
        this.threshold.previous = this.position.previous / viewport;
        this.position.current = position;

        this.el[0].scrollTop = position;
    };

    this.resetScrollPosition = () => {
        this.threshold.previous = 0;
        this.position.previous = 0;
        this.position.current = 0;

        this.el[0].scrollTop = 0;
    };

    this.scrollToBottom = () => {
        this.setScrollPosition(this.getScrollHeight());
    };

    this.lock = () => {
        this.state.locked = true;
    };

    this.unlock = () => {
        this.state.locked = false;
    };

    this.pause = () => {
        this.state.paused = true;
    };

    this.resume = () => {
        this.state.paused = false;
    };

    this.hide = () => {
        if (this.state.hidden) {
            return;
        }

        this.state.hidden = true;
        this.el.css('overflow-y', 'hidden');
    };

    this.unhide = () => {
        if (!this.state.hidden) {
            return;
        }

        this.state.hidden = false;
        this.el.css('overflow-y', 'auto');
    };

    this.isBeyondLowerThreshold = () => {
        const position = this.getScrollPosition();
        const viewport = this.getScrollHeight() - this.getViewableHeight();
        const threshold = position / viewport;

        return (1 - threshold) < OUTPUT_SCROLL_THRESHOLD;
    };

    this.isBeyondUpperThreshold = () => {
        const position = this.getScrollPosition();
        const viewport = this.getScrollHeight() - this.getViewableHeight();
        const threshold = position / viewport;

        return threshold < OUTPUT_SCROLL_THRESHOLD;
    };

    this.isPaused = () => this.state.paused;
    this.isLocked = () => this.state.locked;
    this.isMissing = () => $(OUTPUT_ELEMENT_TBODY)[0].clientHeight < this.getViewableHeight();
}

JobScrollService.$inject = ['$q', '$timeout'];

export default JobScrollService;
