function JobPageService () {
    this.page = null;
    this.resource = null;
    this.result = null;
    this.buffer = null;
    this.cache = null;

    this.init = resource => {
        this.resource = resource;

        this.page = {
            limit: resource.page.pageLimit,
            size: resource.page.size,
            current: 0,
            index: -1,
            count: 0
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

    this.add = (page, position) => {
        page.events = page.events || [];
        page.lines = page.lines || 0;

        if (!position) {
            this.cache.push(page);
        }

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

    this.isOverCapacity = () => {
        return (this.cache.length - this.page.limit) > 0;
    };

    this.trim = () => {
        const count = this.cache.length - this.page.limit;
        const ejected = this.cache.splice(0, count);
        const linesRemoved = ejected.reduce((total, page) => total + page.lines, 0);

        return linesRemoved;
    };

    this.getPageNumber = (page) => {
        let index;

        if (page === 'first') {
            index = 0;
        }

        return this.cache[index].number;
    };

    this.updateLineCount = (page, lines) => {
        let index;

        if (page === 'current') {
            index = this.cache.length - 1;
        }

        if (this.cache[index].lines) {
            this.cache[index].lines += lines;
        } else {
            this.cache[index].lines = lines;
        }
    }

    this.next = () => {

    };

    this.prev = () => {

    };

    this.current = () => {
        return this.resource.model.get(`related.${this.resource.related}.results`);
    };
}

export default JobPageService;
