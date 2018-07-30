import {
    OUTPUT_ELEMENT_CONTAINER,
    OUTPUT_ELEMENT_TBODY,
    OUTPUT_SCROLL_DELAY,
    OUTPUT_SCROLL_THRESHOLD,
} from './constants';

function JobScrollService ($q, $timeout) {
    this.init = ({ next, previous, onLeaveLower, onEnterLower }) => {
        this.el = $(OUTPUT_ELEMENT_CONTAINER);
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
            onLeaveLower,
            onEnterLower,
        };

        this.state = {
            paused: false,
        };

        this.chain = $q.resolve();
        this.el.scroll(this.listen);
    };

    this.listen = () => {
        if (this.isPaused()) {
            return;
        }

        if (this.timer) {
            $timeout.cancel(this.timer);
        }

        this.timer = $timeout(this.register, OUTPUT_SCROLL_DELAY);
    };

    this.isBeyondThreshold = () => {
        const position = this.getScrollPosition();
        const viewport = this.getScrollHeight() - this.getViewableHeight();
        const threshold = position / viewport;

        return (1 - threshold) < OUTPUT_SCROLL_THRESHOLD;
    };

    this.register = () => {
        this.pause();

        const position = this.getScrollPosition();
        const viewport = this.getScrollHeight() - this.getViewableHeight();

        const threshold = position / viewport;
        const downward = position > this.position.previous;

        const isBeyondUpperThreshold = threshold < OUTPUT_SCROLL_THRESHOLD;
        const isBeyondLowerThreshold = (1 - threshold) < OUTPUT_SCROLL_THRESHOLD;

        const wasBeyondUpperThreshold = this.threshold.previous < OUTPUT_SCROLL_THRESHOLD;
        const wasBeyondLowerThreshold = (1 - this.threshold.previous) < OUTPUT_SCROLL_THRESHOLD;

        const transitions = [];

        if (position <= 0 || (isBeyondUpperThreshold && !wasBeyondUpperThreshold)) {
            transitions.push(this.hooks.previous);
        }

        if (!isBeyondLowerThreshold && wasBeyondLowerThreshold) {
            transitions.push(this.hooks.onLeaveLower);
        }

        if (isBeyondLowerThreshold && !wasBeyondLowerThreshold) {
            transitions.push(this.hooks.onEnterLower);
            transitions.push(this.hooks.next);
        } else if (threshold >= 1) {
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
                this.resume();
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

    this.resume = () => {
        this.state.paused = false;
    };

    this.pause = () => {
        this.state.paused = true;
    };

    this.isMissing = () => $(OUTPUT_ELEMENT_TBODY)[0].clientHeight < this.getViewableHeight();
    this.isPaused = () => this.state.paused;
}

JobScrollService.$inject = ['$q', '$timeout'];

export default JobScrollService;
