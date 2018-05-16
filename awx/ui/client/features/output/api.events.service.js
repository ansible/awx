const PAGE_LIMIT = 5;
const PAGE_SIZE = 50;

const BASE_PARAMS = {
    order_by: 'start_line',
    page_size: PAGE_SIZE,
};

const merge = (...objs) => _.merge({}, ...objs);

const getInitialState = params => ({
    results: [],
    count: 0,
    previous: 1,
    page: 1,
    next: 1,
    last: 1,
    params: merge(BASE_PARAMS, params),
});

function JobEventsApiService ($http, $q) {
    this.init = (endpoint, params) => {
        this.keys = [];
        this.cache = {};
        this.pageSizes = {};
        this.endpoint = endpoint;
        this.state = getInitialState(params);
    };

    this.getLastPage = count => Math.ceil(count / this.state.params.page_size);

    this.fetch = () => {
        delete this.cache;
        delete this.keys;
        delete this.pageSizes;

        this.cache = {};
        this.keys = [];
        this.pageSizes = {};

        return this.getPage(1).then(() => this);
    };

    this.getPage = number => {
        if (number < 1 || number > this.state.last) {
            return $q.resolve();
        }

        if (this.cache[number]) {
            if (this.pageSizes[number] === PAGE_SIZE) {
                return this.cache[number];
            }

            delete this.pageSizes[number];
            delete this.cache[number];

            this.keys.splice(this.keys.indexOf(number));
        }

        const { params } = this.state;

        delete params.page;

        params.page = number;

        const promise = $http.get(this.endpoint, { params })
            .then(({ data }) => {
                const { results, count } = data;

                this.state.results = results;
                this.state.count = count;
                this.state.page = number;
                this.state.last = this.getLastPage(count);
                this.state.previous = Math.max(1, number - 1);
                this.state.next = Math.min(this.state.last, number + 1);

                this.pageSizes[number] = results.length;

                return { results, page: number };
            });

        this.cache[number] = promise;
        this.keys.push(number);

        if (this.keys.length > PAGE_LIMIT) {
            delete this.cache[this.keys.shift()];
        }

        return promise;
    };

    this.first = () => this.getPage(1);
    this.next = () => this.getPage(this.state.next);
    this.previous = () => this.getPage(this.state.previous);

    this.last = () => {
        const params = merge({}, this.state.params);

        delete params.page;
        delete params.order_by;

        params.page = 1;
        params.order_by = '-start_line';

        const promise = $http.get(this.endpoint, { params })
            .then(({ data }) => {
                const { results, count } = data;
                const lastPage = this.getLastPage(count);

                results.reverse();
                const shifted = results.splice(count % PAGE_SIZE);

                this.state.results = shifted;
                this.state.count = count;
                this.state.page = lastPage;
                this.state.next = lastPage;
                this.state.last = lastPage;
                this.state.previous = Math.max(1, this.state.page - 1);

                return { results: shifted, page: lastPage };
            });

        return promise;
    };
}

JobEventsApiService.$inject = [
    '$http',
    '$q'
];

export default JobEventsApiService;
