import Ansi from 'ansi-to-html';
import hasAnsi from 'has-ansi';

const templateUrl = require('~components/output/stdout.partial.html');

let $sce;
let $timeout;
let ansi;

function atOutputStdoutLink (scope, element, attrs, controller) {
    controller.init(scope, element);
}

function AtOutputStdoutController (_$sce_, _$timeout_) {
    const vm = this || {};

    $timeout = _$timeout_;
    $sce = _$sce_;
    ansi = new Ansi();

    let scope;
    let element;

    vm.init = (_scope_, _element_) => {
        scope = _scope_;
        element = _element_;

        scope.$watch('state.stdout', curr => {
            if (!curr) {
                return;
            }

            render(scope.state.stdout);
        });
    };

    vm.scroll = position => {
        const container = element.find('.at-Stdout-container')[0];

        if (position === 'bottom') {
            container.scrollTop = container.scrollHeight;
        } else {
            container.scrollTop = 0;
        }
    };
}

AtOutputStdoutController.$inject = [
    '$sce',
    '$timeout',
];

function render (stdout) {
    console.log('render');
    const html = $sce.trustAsHtml(parseStdout(stdout));

    $timeout(() => {
        const table = $('#atStdoutTBody');

        table.html($sce.getTrustedHtml(html));
    });
}

function parseStdout (stdout) {
    const lines = stdout.split('\r\n');

    let ln = 0;

    return lines.reduce((html, line) => {
        ln++;

        return `${html}${createRow(ln, line)}`;
    }, '');
}

function createRow (ln, content) {
    content = content || '';

    if (hasAnsi(content)) {
        content = ansi.toHtml(content);
    }

    return `
        <tr>
            <td class="at-Stdout-line">${ln}</td>
            <td class="at-Stdout-event">${content}</td>
        </tr>`;
}
function atOutputStdout () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: 'atOutputStdout',
        templateUrl,
        controller: AtOutputStdoutController,
        controllerAs: 'vm',
        link: atOutputStdoutLink,
        scope: {
            state: '=',
        }
    };
}

export default atOutputStdout;
