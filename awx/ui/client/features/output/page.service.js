function JobPageService ($q) {
    this.init = ({ resource }) => {
        this.resource = resource;

        this.page = {
            limit: this.resource.page.pageLimit,
            size: this.resource.page.size,
            cache: [],
            state: {
                count: 0,
                current: 0,
                first: 0,
                last: 0
            }
        };

        this.bookmark = {
            pending: false,
            set: false,
            cache: [],
            state: {
                count: 0,
                first: 0,
                last: 0,
                current: 0
            }
        };

        this.result = {
            limit: this.page.limit * this.page.size,
            count: 0
        };

        this.buffer = {
            count: 0
        };
    };

    this.addPage = (number, events, push, reference) => {
        const page = { number, events, lines: 0 };
        reference = reference || this.getActiveReference();

        if (push) {
            reference.cache.push(page);
            reference.state.last = page.number;
            reference.state.first = reference.cache[0].number;
        } else {
            reference.cache.unshift(page);
            reference.state.first = page.number;
            reference.state.last = reference.cache[reference.cache.length -1].number;
        }

        reference.state.current = page.number;
        reference.state.count++;
    };

    this.addToBuffer = event => {
        const reference = this.getReference();
        const index = reference.cache.length - 1;
        let pageAdded = false;

        if (this.result.count % this.page.size === 0) {
            this.addPage(reference.state.current + 1, [event], true, reference);

            if (this.isBookmarkPending()) {
                this.setBookmark();
            }

            this.trimBuffer();

            pageAdded = true;
        } else {
            reference.cache[index].events.push(event);
        }

        this.buffer.count++;
        this.result.count++;

        return pageAdded;
    };

    this.trimBuffer = () => {
        const reference = this.getReference();
        const diff = reference.cache.length - this.page.limit;

        if (diff <= 0) {
            return;
        }

        for (let i = 0; i < diff; i++) {
            if (reference.cache[i].events) {
                this.buffer.count -= reference.cache[i].events.length;
                reference.cache[i].events.splice(0, reference.cache[i].events.length);
            }
        }
    };

    this.isBufferFull = () => {
        if (this.buffer.count === 2) {
            return true;
        }

        return false;
    }

    this.emptyBuffer = () => {
        const reference = this.getReference();
        let data = [];

        for (let i = 0; i < reference.cache.length; i++) {
            const count = reference.cache[i].events.length;

            if (count > 0) {
                this.buffer.count -= count;
                data = data.concat(reference.cache[i].events.splice(0, count));
            }
        }

        return data;
    };

    this.emptyCache = number => {
        const reference = this.getActiveReference();

        number = number || reference.state.current;

        reference.state.first = number;
        reference.state.last = number;
        reference.state.current = number;
        reference.cache.splice(0, reference.cache.length);
    };

    this.isOverCapacity = () => {
        const reference = this.getActiveReference();

        return (reference.cache.length - this.page.limit) > 0;
    };

    this.trim = left => {
        let reference = this.getActiveReference();
        let excess = reference.cache.length - this.page.limit;
        let ejected;

        if (left) {
            ejected = reference.cache.splice(0, excess);
            reference.state.first = reference.cache[0].number;
        } else {
            ejected = reference.cache.splice(-excess);
            reference.state.last = reference.cache[reference.cache.length - 1].number;
        }

        return ejected.reduce((total, page) => total + page.lines, 0);
    };

    this.isPageBookmarked = number => {
        return number >= this.page.bookmark.first && number <= this.page.bookmark.last;
    };

    this.updateLineCount = (lines, stream) => {
        let reference;

        if (stream) {
            reference = this.getReference();
        } else {
            reference = this.getActiveReference();
        }

        const index = reference.cache.findIndex(item => item.number === reference.state.current);

        reference.cache[index].lines += lines;
    }

    this.isBookmarkPending = () => {
        return this.bookmark.pending;
    };

    this.isBookmarkSet = () => {
        return this.bookmark.set;
    };

    this.setBookmark = () => {
        if (this.isBookmarkSet()) {
            return;
        }

        if (!this.isBookmarkPending()) {
            this.bookmark.pending = true;

            return;
        }

        this.bookmark.state.first = this.page.state.first - 1;
        this.bookmark.state.last = this.page.state.last  - 1;
        this.bookmark.state.current = this.page.state.current - 1;
        this.bookmark.cache = JSON.parse(JSON.stringify(this.page.cache));
        this.bookmark.set = true;
        this.bookmark.pending = false;
    };

    this.removeBookmark = () => {
        this.bookmark.set = false;
        this.bookmark.pending = false;
        this.bookmark.cache.splice(0, this.bookmark.cache.length);
        this.bookmark.state.first = 0;
        this.bookmark.state.last = 0;
        this.bookmark.state.current = 0;
    };

    this.next = () => {
        const reference = this.getActiveReference();
        const config = this.buildRequestConfig(reference.state.last + 1);

        return this.resource.model.goToPage(config)
            .then(data => {
                if (!data || !data.results) {
                    return $q.resolve();
                }

                this.addPage(data.page, [], true);

                return data.results;
            });
    };

    this.previous = () => {
        const reference = this.getActiveReference();
        const config = this.buildRequestConfig(reference.state.first - 1);

        return this.resource.model.goToPage(config)
            .then(data => {
                if (!data || !data.results) {
                    return $q.resolve();
                }

                this.addPage(data.page, [], false);

                return data.results;
            });
    };

    this.last = () => {
        const config = this.buildRequestConfig('last');

        return this.resource.model.goToPage(config)
            .then(data => {
                if (!data || !data.results) {
                    return $q.resolve();
                }

                this.emptyCache(data.page);
                this.addPage(data.page, [], true);

                return data.results;
            });
    };

    this.first = () => {
        const config = this.buildRequestConfig('first');

        return this.resource.model.goToPage(config)
            .then(data => {
                if (!data || !data.results) {
                    return $q.resolve();
                }

                this.emptyCache(data.page);
                this.addPage(data.page, [], false);

                return data.results;
            });
    };

    this.buildRequestConfig = number => {
        return {
            page: number,
            related: this.resource.related,
            params: {
                order_by: 'start_line'
            }
        };
    };

    this.getActiveReference = () => {
        return this.isBookmarkSet() ? this.getReference(true) : this.getReference();
    };

    this.getReference = (bookmark) => {
        if (bookmark) {
            return {
                bookmark: true,
                cache: this.bookmark.cache,
                state: this.bookmark.state
            };
        }

        return {
            bookmark: false,
            cache: this.page.cache,
            state: this.page.state
        };
    };
}

JobPageService.$inject = ['$q'];

export default JobPageService;
