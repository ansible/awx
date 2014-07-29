/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventoryGroups.js
 *
 *  Help object for inventory groups/hosts page.
 *
 *  @dict
 */

'use strict';

angular.module('InventoryGroupsHelpDefinition', [])
    .value('InventoryGroupsHelp', {
        story: {
            hdr: 'Building your inventory',
            width: 510,
            height: 560,
            steps: [{
                intro: 'Start by creating a group:',
                img: {
                    src: 'groups001.png',
                    maxWidth: 338,
                    maxHeight: 222
                },
                box: "Click <i class=\"fa fa-plus\"></i> on the groups list (the left side of the page) to add a new group.",
                autoOffNotice: true
            }, {
                intro: 'Enter group properties:',
                img: {
                    src: 'groups002.png',
                    maxWidth: 443,
                    maxHeight: 251
                },
                box: 'Enter the group name, a description and any inventory variables. Variables can be entered using either JSON or YAML syntax. ' +
                    'For more on inventory variables, see <a href=\"http://docs.ansible.com/intro_inventory.html\" target="_blank"> ' +
                    'docs.ansible.com/intro_inventory.html</a>'
            }, {
                intro: 'Cloud inventory: select cloud source',
                img: {
                    src: 'groups003.png',
                    maxWidth: 412,
                    maxHeight: 215
                },
                box: "For a cloud inventory, choose the cloud provider from the list and select your credentials. If you have not already setup " +
                    "credentials for the provider, you will need to do that first on the <a href=\"/#/credentials\" " +
                    "target=\"_blank\">Credentials</a> tab."
            }, {
                intro: 'Cloud inventory: synchronize Tower with the cloud',
                img: {
                    src: 'groups004.png',
                    maxWidth: 261,
                    maxHeight: 221
                },
                box: "To pull the cloud inventory into Tower, initiate an inventory sync by clicking <i class=\"fa fa-exchange\"></i>."
            }, {
                intro: "Groups can have subgroups:",
                img: {
                    src: 'groups008.png',
                    maxWidth: 380,
                    maxHeight: 231
                },
                box: "<div class=\"text-left\">First, select a group.</div>"
            }, {
                intro: "Groups can have subgroups:",
                img: {
                    src: 'groups009.png',
                    maxWidth: 400,
                    maxHeight: 132
                },
                box: "<div class=\"text-left\">Then click <i class=\"fa fa-plus\"></i> to create a new group. The new group " +
                    "will be added to the selected group.</div>"
            }, {
                intro: 'Adding hosts:',
                img: {
                    src: 'groups010.png',
                    maxWidth: 400,
                    maxHeight: 122
                },
                box: "<div class=\"text-left\"><p>First, select a Group. " +
                    "Then click <i class=\"fa fa-plus\"></i> on the hosts list (the right side of the page) to create a host. " +
                    "The new host will be part of the selected group.</p></div>"
            }]
        }
    });
