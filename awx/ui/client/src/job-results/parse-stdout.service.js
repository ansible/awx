/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

export default [function(){
    var val = {
        prettify: function(line){
            // TODO: figure out from Jared what this is

            if (line.indexOf("[K") > -1) {
                console.log(line);
            }

            line = line.replace(/u001b/g, '');

            // ansi classes
            line = line.replace(/\[1;31m/g, '<span class="ansi1 ansi31">');
            line = line.replace(/\[0;31m/g, '<span class="ansi1 ansi31">');
            line = line.replace(/\[0;32m/g, '<span class="ansi32">');
            line = line.replace(/\[0;32m=/g, '<span class="ansi32">');
            line = line.replace(/\[0;32m1/g, '<span class="ansi36">');
            line = line.replace(/\[0;33m/g, '<span class="ansi33">');
            line = line.replace(/\[0;34m/g, '<span class="ansi34">');
            line = line.replace(/\[0;35m/g, '<span class="ansi35">');
            line = line.replace(/\[0;36m/g, '<span class="ansi36">');
            line = line.replace(/(<host.*?>)\s/g, '$1');

            //end span
            line = line.replace(/\[0m/g, '</span>');
            return line;
        },
        getCollapseClasses: function(event, line, lineNum) {
            var string = "";
            if (event.event_name === "playbook_on_play_start") {
                string += " header_play";
                string += " header_play_" + event.event_data.play_uuid;
                if (line) {
                    string += " actual_header";
                }
            } else if (event.event_name === "playbook_on_task_start") {
                string += " header_task";
                string += " header_task_" + event.event_data.task_uuid;
                if (event.event_data.play_uuid) {
                    string += " play_" + event.event_data.play_uuid;
                }
                if (line) {
                    string += " actual_header";
                }
            } else {
                if (event.event_data.play_uuid) {
                    string += " play_" + event.event_data.play_uuid;
                }
                if (event.event_data.task_uuid) {
                    string += " task_" + event.event_data.task_uuid;
                }
            }
            string += " line_num_" + lineNum;
            return string;
        },
        getCollapseIcon: function(event, line) {
            var clickClass,
                expanderizerSpecifier;

            var emptySpan = `
<span class="JobResultsStdOut-lineExpander"></span>`;

            if ((event.event_name === "playbook_on_play_start" ||
                event.event_name === "playbook_on_task_start") &&
                line !== "") {
                    if (event.event_name === "playbook_on_play_start" &&
                        line.indexOf("PLAY") > -1) {
                            expanderizerSpecifier = "play";
                            clickClass = "play_" +
                                event.event_data.play_uuid;
                    } else if (line.indexOf("TASK") > -1 ||
                        line.indexOf("RUNNING HANDLER") > -1) {
                            expanderizerSpecifier = "task";
                            clickClass = "task_" +
                                event.event_data.task_uuid;
                    } else {
                        return emptySpan;
                    }

                return `
<span class="JobResultsStdOut-lineExpander">
    <i class="JobResultsStdOut-lineExpanderIcon fa fa-caret-down expanderizer
        expanderizer--${expanderizerSpecifier} expanded"
        ng-click="toggleLine($event, '.${clickClass}')"
        data-uuid="${clickClass}">
    </i>
</span>`;
            } else {
                return emptySpan;
            }
        },
        parseStdout: function(event){
            return _
                .zip(_.range(event.start_line + 1,
                    event.end_line + 1),
                    event.stdout.replace("\t", "        ").split("\r\n").slice(0, -1))
                .map(lineArr => {
                    return `
<div class="JobResultsStdOut-aLineOfStdOut${this.getCollapseClasses(event, lineArr[1], lineArr[0])}">
    <div class="JobResultsStdOut-lineNumberColumn">${this.getCollapseIcon(event, lineArr[1])}${lineArr[0]}</div>
    <div class="JobResultsStdOut-stdoutColumn">${this.prettify(lineArr[1])}</div>
</div>`;
                }).join("");
        }
    };
    return val;
}];
