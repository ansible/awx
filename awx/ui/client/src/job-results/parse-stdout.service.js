/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

export default [function(){
    var val = {
        prettify: function(line){

            // this function right now just removes the 'rn' strings
            // that i'm currently seeing on this branch on the beginning
            // and end of each event string. In the future it could be
            // used to add styling classes to the actual lines of stdout
            // line = line.replace(/rn/g, '\n');
            line = line.replace(/u001b/g, '');

            // ok
            line = line.replace(/\[0;32m/g, '<span class="ansi32">');

            //unreachable
            line = line.replace(/\[1;31m/g, '<span class="ansi1 ansi31">');
            line = line.replace(/\[0;31m/g, '<span class="ansi1 ansi31">');

            line = line.replace(/\[0;32m=/g, '<span class="ansi32">');
            line = line.replace(/\[0;32m1/g, '<span class="ansi36">');
            line = line.replace(/\[0;33m/g, '<span class="ansi33">');
            line = line.replace(/\[0;36m/g, '<span class="ansi36">');

            //end span
            line = line.replace(/\[0m/g, '</span>');
            return line;
        },
        getCollapseClasses: function(event) {
            var string = "";
            if (event.event_name === "playbook_on_play_start") {
                return string;
            } else if (event.event_name === "playbook_on_task_start") {
                if (event.event_data.play_uuid) {
                    string += " play_" + event.event_data.play_uuid;
                }
                return string;
            } else {
                if (event.event_data.play_uuid) {
                    string += " play_" + event.event_data.play_uuid;
                }
                if (event.event_data.task_uuid) {
                    string += " task_" + event.event_data.task_uuid;
                }
                return string;
            }
        },
        getCollapseIcon: function(event, line) {
            if ((event.event_name === "playbook_on_play_start" || event.event_name === "playbook_on_task_start") && line !== "") {
                return `<span class="JobResultsStdOut-lineExpander"><i class="fa fa-caret-down"></i></span>`;
            } else {
                return `<span class="JobResultsStdOut-lineExpander"></span>`;
            }
        },
        parseStdout: function(event){
            var stdoutStrings = _
                .zip(_.range(event.start_line + 1,
                    event.end_line + 1),
                    event.stdout.split("\r\n").slice(0, -1))
                .map(lineArr => {
                    return `
<div class="JobResultsStdOut-aLineOfStdOut${this.getCollapseClasses(event)}">
    <div class="JobResultsStdOut-lineNumberColumn">${this.getCollapseIcon(event, lineArr[1])}${lineArr[0]}</div>
    <div class="JobResultsStdOut-stdoutColumn">${this.prettify(lineArr[1])}</div>
</div>`;
                }).join("");
            // this object will be used by the ng-repeat in the
            // job-results-stdout.partial.html. probably need to add the
            // elapsed time in here too
            return stdoutStrings;
        }
    };
    return val;
}];
