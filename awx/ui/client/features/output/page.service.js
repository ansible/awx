function JobPageService ($q) {
    this.init = resource => {
        this.resource = resource;

        this.page = {
            limit: this.resource.page.pageLimit,
            size: this.resource.page.size,
            current: 0,
            index: -1,
            count: 0,
            first: 0,
            last: 0,
            bookmark: {
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

        this.cache = [];
    };

    this.add = (page, position, bookmark) => {
        page.events = page.events || [];
        page.lines = page.lines || 0;

        if (position === 'first') {
            this.cache.unshift(page);
            this.page.first = page.number;
            this.page.last = this.cache[this.cache.length -1].number;
        } else {
            this.cache.push(page);
            this.page.last = page.number;
            this.page.first = this.cache[0].number;
        }

        if (bookmark) {
            this.page.bookmark.current = page.number;
        }

        this.page.current = page.number;
        this.page.count++;
    };

    this.addToBuffer = event => {
        let pageAdded = false;

        if (this.result.count % this.page.size === 0) {
            pageAdded = true;

            this.add({ number: this.page.count + 1, events: [event] });

            this.trimBuffer();
        } else {
            this.cache[this.cache.length - 1].events.push(event);
        }

        this.buffer.count++;
        this.result.count++;

        return pageAdded;
    };

    this.trimBuffer = () => {
        const diff = this.cache.length - this.page.limit;

        if (diff <= 0) {
            return;
        }

        for (let i = 0; i < diff; i++) {
            if (this.cache[i].events) {
                this.buffer.count -= this.cache[i].events.length;
                this.cache[i].events = [];
            }
        }
    };

    this.emptyBuffer = () => {
        let data = [];

        for (let i = 0; i < this.cache.length; i++) {
            const events = this.cache[i].events;

            if (events.length > 0) {
                this.buffer.count -= events.length;
                data = data.concat(this.cache[i].events.splice(0, events.length));
            }
        }

        return data;
    };

    this.emptyCache = () => {
        this.page.first = this.page.current;
        this.page.last = this.page.current;
        this.cache = [];
    };

    this.isOverCapacity = () => {
        return (this.cache.length - this.page.limit) > 0;
    };

    this.trim = side => {
        const count = this.cache.length - this.page.limit;

        let ejected;

        if (side === 'left') {
            ejected = this.cache.splice(0, count);
            this.page.first = this.cache[0].number;
        } else {
            ejected = this.cache.splice(-count);
            this.page.last = this.cache[this.cache.length - 1].number;
        }

        return ejected.reduce((total, page) => total + page.lines, 0);
    };

    this.getPageNumber = page => {
        let index;

        if (page === 'first') {
            index = 0;
        }

        return this.cache[index].number;
    };

    this.updateLineCount = (page, lines) => {
        let index;

        if (page === 'current') {
            index = this.cache.findIndex(item => item.number === this.page.current);
        }

        this.cache[index].lines += lines;
    }

    this.bookmark = () => {
        if (!this.page.bookmark.active) {
            this.page.bookmark.first = this.page.first;
            this.page.bookmark.last = this.page.last;
            this.page.bookmark.current = this.page.current;
            this.page.bookmark.active = true;
        } else {
            this.page.bookmark.active = false;
        }
    };

    this.next = () => {
        let page;
        let bookmark;

        if (this.page.bookmark.active) {
            page = this.page.bookmark.current + 1;
            bookmark = true;
        } else {
            page = this.page.last + 1;
        }

        const config = this.buildRequestConfig(page);

        return this.resource.model.goToPage(config)
            .then(data => {
                if (!data || !data.results) {
                    return $q.resolve();
                }

                this.add({ number: data.page, events: [], lines: 0 }, 'last', bookmark);

                return data.results;
            });
    };

    this.previous = () => {
        let page;
        let bookmark;

        if (this.page.bookmark.active) {
            page = this.page.bookmark.current - 1;
            bookmark = true;
        } else {
            page = this.page.first - 1;
        }

        const config = this.buildRequestConfig(page);

        return this.resource.model.goToPage(config)
            .then(data => {
                if (!data || !data.results) {
                    return $q.resolve();
                }

                this.add({ number: data.page, events: [], lines: 0 }, 'first', bookmark);

                return data.results;
            });
    };

    this.last = () => {
        const config = this.buildRequestConfig('last');

        this.emptyCache();

        return this.resource.model.goToPage(config)
            .then(data => {
                if (!data || !data.results) {
                    return $q.resolve();
                }

                this.add({ number: data.page, events: [], lines: 0 }, 'last');

                return data.results;
            });
    };

    this.first = () => {
        const config = this.buildRequestConfig('first');

        this.emptyCache();

        return this.resource.model.goToPage(config)
            .then(data => {
                if (!data || !data.results) {
                    return $q.resolve();
                }

                this.add({ number: data.page, events: [], lines: 0 }, 'first');

                return data.results;
            });
    };

    this.buildRequestConfig = (page) => {
        return {
            page,
            related: this.resource.related,
            params: {
                order_by: 'start_line'
            }
        };
    };

    this.current = () => {
        return this.resource.model.get(`related.${this.resource.related}.results`);
    };
}

JobPageService.$inject = ['$q'];

export default JobPageService;
