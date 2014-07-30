/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  FirefoxSocketHelp.js
 *
 *  Help object for socket connection troubleshooting
 *
 */

'use strict';

angular.module('FFSocketHelpDefinition', [])
    .value('FFSocketHelp', {
        story: {
            hdr: 'Live Events',
            width: 510,
            height: 560,
            steps: [{
                intro: 'Connection status indicator:',
                img: {
                    src: 'socket_indicator.png',
                    maxWidth: 360
                },
                box: "<p>When live events are streaming the connection status indicator will be green. Red or orange indicates the " +
                    "browser is having difficulty connecting to the server, and live events are no longer being received.</p><p>If the indicator " +
                    "appears red or orange, click Next for troubleshooting help.</p>"
            }, {
                intro: 'Live events connection:',
                icon: {
                    "class": "fa fa-5x fa-rss {{ socketStatus }}-color",
                    style: "margin-top: 75px;",
                    containerHeight: 200
                },
                box: "<p><strong>{{ browserName }}</strong> is connecting to the live events server on port <strong>{{ socketPort }}</strong>. The current connection status is " +
                    "<i class=\"fa icon-socket-{{ socketStatus }}\"></i> <strong>{{ socketStatus }}</strong>.</p><p>If the connection status indicator is not green, have the " +
                    "system administrator verify this is the correct port and that access to the port is not blocked by a firewall.</p>"
            }, {
                intro: 'Self signed certificate:',
                icon: {
                    "class": "fa fa-5x fa-check ok-color",
                    style: "margin-top: 75px;",
                    containerHeight: 200
                },
                box: "<p>If the Tower web server is using a self signed security certificate, Firefox needs to accept the certificate and allow the " +
                    "connection.</p><p>Click Next for help accepting a self signed certificate.</p>"
            }, {
                intro: 'Accepting a self-signed certificate:',
                img: {
                    src: 'understand_the_risk.png',
                    maxWidth: 440
                },
                box: "<p>Navigate to <a href=\"{{ socketURL }}\" target=\"_blank\">{{ socketURL }}</a> The above warning will appear.</p><p>Click <i>I Understand the Risks</i></p>"
            }, {
                intro: 'Accepting a self-signed certificate:',
                img: {
                    src: 'add_exception.png',
                    maxWidth: 440
                },
                box: "<p>Click the <i>Add Exception</i> button."
            }, {
                intro: 'Accepting a self-signed certificate:',
                img: {
                    src: 'confirm_exception.png',
                    maxWidth: 340
                },
                box: "<p>Click the <i>Confirm the Security Exception</i> button. This will add the self signed certificate from the Tower server to Firefox's list of trusted certificates.<p>"
            }, {
                intro: 'Accepting a self-signed certificate:',
                img: {
                    src: 'refresh_firefox.png',
                    maxWidth: 480
                },
                box: "<p>Now that Firefox has accepted the security certificate the live event connection status indicator should turn green. If it does not, reload Tower by clicking the " +
                    "Firefox refresh button."
            }]
        }
    });
