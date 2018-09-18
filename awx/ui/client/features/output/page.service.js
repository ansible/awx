/* eslint camelcase: 0 */
import { OUTPUT_PAGE_LIMIT } from './constants';

function PageService ($q) {
    this.init = ({ getPage, getFirst, getLast, getLastPageNumber }) => {
        this.api = {
            getPage,
            getFirst,
            getLast,
            getLastPageNumber,
        };
        this.pages = {};
        this.state = { head: 0, tail: 0 };
    };

    this.getNext = () => {
        const lastPageNumber = this.api.getLastPageNumber();
        const number = Math.min(this.state.tail + 1, lastPageNumber);

        if (number < 1) {
            return $q.resolve([]);
        }

        if (number > lastPageNumber) {
            return $q.resolve([]);
        }

        let promise;

        if (this.pages[number]) {
            promise = $q.resolve(this.pages[number]);
        } else {
            promise = this.api.getPage(number);
        }

        return promise
            .then(results => {
                if (results.length <= 0) {
                    return $q.resolve([]);
                }

                this.state.tail = number;
                this.pages[number] = results;

                return $q.resolve(results);
            });
    };

    this.getPrevious = () => {
        const number = Math.max(this.state.head - 1, 1);

        if (number < 1) {
            return $q.resolve([]);
        }

        if (number > this.api.getLastPageNumber()) {
            return $q.resolve([]);
        }

        let promise;

        if (this.pages[number]) {
            promise = $q.resolve(this.pages[number]);
        } else {
            promise = this.api.getPage(number);
        }

        return promise
            .then(results => {
                if (results.length <= 0) {
                    return $q.resolve([]);
                }

                this.state.head = number;
                this.pages[number] = results;

                return $q.resolve(results);
            });
    };

    this.getLast = () => this.api.getLast()
        .then(results => {
            if (results.length <= 0) {
                return $q.resolve([]);
            }

            const number = this.api.getLastPageNumber();

            this.state.head = number;
            this.state.tail = number;
            this.pages[number] = results;

            return $q.resolve(results);
        });

    this.getFirst = () => this.api.getFirst()
        .then(results => {
            if (results.length <= 0) {
                return $q.resolve([]);
            }

            this.state.head = 1;
            this.state.tail = 1;
            this.pages[1] = results;

            return $q.resolve(results);
        });

    this.trimTail = () => {
        const { tail, head } = this.state;
        let popCount = 0;

        for (let i = tail; i > head; i--) {
            if (!this.isOverCapacity()) {
                break;
            }

            if (this.pages[i]) {
                popCount += this.pages[i].length;
            }

            delete this.pages[i];

            this.state.tail--;
        }

        return popCount;
    };

    this.trimHead = () => {
        const { head, tail } = this.state;
        let popCount = 0;

        for (let i = head; i < tail; i++) {
            if (!this.isOverCapacity()) {
                break;
            }

            if (this.pages[i]) {
                popCount += this.pages[i].length;
            }

            delete this.pages[i];

            this.state.head++;
        }

        return popCount;
    };

    this.isOverCapacity = () => this.state.tail - this.state.head > OUTPUT_PAGE_LIMIT;
}

PageService.$inject = ['$q'];

export default PageService;
