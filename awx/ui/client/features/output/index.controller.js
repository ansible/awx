import Ansi from 'ansi-to-html';
import hasAnsi from 'has-ansi';

function JobsIndexController (job, $sce) {
    const vm = this || {};
    const results = job.get('related.job_events.results');
    const ansi = new Ansi({});

    /*
     *    const colors = [];
     *
     *    for (let i = 0; i < 255; i++) {
     *        colors.push('#ababab');
     *    }
     *
     */

    let html = '';
    results.forEach((line, i) => {
        if (!line.stdout) {
            return;
        }

        let output;

        if (hasAnsi(line.stdout)) {
            output = ansi.toHtml(line.stdout);
        } else {
            output = line.stdout; // .replace(/(\n|\r)/g, '');
        }

        html += `<tr><td>${i}</td><td>${output}</td></tr>`;
    });

    vm.html = $sce.trustAsHtml(html);
}

JobsIndexController.$inject = ['job', '$sce'];

module.exports = JobsIndexController;
