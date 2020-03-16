export default
    function SetStatus($filter, SetEnabledMsg, Empty, i18n) {
        return function(params) {
            var scope = params.scope,
            host = params.host,
            i, html, title;

            function ellipsis(a) {
                if (a.length > 25) {
                    return a.substr(0,25) + '...';
                }
                return a;
            }

            function noRecentJobs() {
                title = i18n._('No job data');
                html = "<p>" + i18n._("No recent job data available for this host.") + "</p>\n";
            }

            function setMsg(host) {
                var j, job, jobs;

                if (host.has_active_failures === true || (host.has_active_failures === false && host.last_job !== null)) {
                    if (host.has_active_failures === true) {
                        host.badgeToolTip = i18n._('Most recent job failed. Click to view jobs.');
                        host.active_failures = 'error';
                    }
                    else {
                        host.badgeToolTip = i18n._("Most recent job successful. Click to view jobs.");
                        host.active_failures = 'successful';
                    }
                    if (host.summary_fields.recent_jobs.length > 0) {
                        // build html table of job status info
                        jobs = host.summary_fields.recent_jobs.sort(
                            function(a,b) {
                            // reverse numerical order
                            return -1 * (a - b);
                        });
                        title = "Recent Jobs";
                        html = "<table class=\"table table-condensed flyout\" style=\"width: 100%\">\n";
                        html += "<thead>\n";
                        html += "<tr>\n";
                        html += "<th>" + i18n._("Status") + "</th>\n";
                        html += "<th>" + i18n._("Finished") + "</th>\n";
                        html += "<th>" + i18n._("Name") + "</th>\n";
                        html += "</tr>\n";
                        html += "</thead>\n";
                        html += "<tbody>\n";
                        for (j=0; j < jobs.length; j++) {
                            job = jobs[j];
                            html += "<tr>\n";

                            // SmartStatus-tooltips are named --success whereas icon-job uses successful
                            var iconStatus = (job.status === 'successful') ? 'success' : 'failed';

                            html += "<td><a aria-label=\"{{'View job' | translate}}\" href=\"#/jobs/" + job.id + "\"><i class=\"fa DashboardList-status SmartStatus-tooltip--" + iconStatus + " icon-job-" +
                                job.status + "\"></i></a></td>\n";

                            html += "<td>" + ($filter('longDate')(job.finished)).replace(/ /,'<br />') + "</td>\n";

                            html += "<td class=\"break\"><a href=\"#/jobs/" + job.id + "\" " +
                                "aw-tool-tip=\"" + job.status.charAt(0).toUpperCase() + job.status.slice(1) +
                                ". Click for details\" data-placement=\"top\">" + $filter('sanitize')(ellipsis(job.name)) + "</a></td>\n";

                            html += "</tr>\n";
                        }
                        html += "</tbody>\n";
                        html += "</table>\n";
                    }
                    else {
                        noRecentJobs();
                    }
                }
                else if (host.has_active_failures === false && host.last_job === null) {
                    host.badgeToolTip = i18n._("No job data available.");
                    host.active_failures = 'none';
                    noRecentJobs();
                }
                host.job_status_html = html;
                host.job_status_title = title;
            }

            if (!Empty(host)) {
                // update single host
                setMsg(host);
                SetEnabledMsg(host);
            }
            else {
                // update all hosts
                for (i=0; i < scope.hosts.length; i++) {
                    setMsg(scope.hosts[i]);
                    SetEnabledMsg(scope.hosts[i]);
                }
            }
        };
    }

SetStatus.$inject =
    [   '$filter',
        'SetEnabledMsg',
        'Empty',
        'i18n'
    ];
