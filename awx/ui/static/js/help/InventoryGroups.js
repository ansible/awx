/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventoryGroups.js 
 *
 *  Help object for inventory groups/hosts page.
 *
 *  @dict
 */
angular.module('InventoryGroupsHelpDefinition', [])
    .value(
    'InventoryGroupsHelp', {
        story: {
            hdr: 'Building your inventory',
            steps: {
                step1: {
                    intro: 'Start by creating a group:',
                    img: { src: 'groups001.png', maxWidth: 338 , maxHeight: 222 },
                    box: "Click <i class=\"fa fa-plus\"></i> on the groups list (the left side of the page) to add a new group.",
                    autoOffNotice: true,
                    height: 500
                    },
                step2: {
                    intro: ' ',
                    img: { src: 'groups002.png', maxWidth: 443, maxHeight: 251 },
                    box: "Provide a name, description and any variables.",
                    height: 500
                    },
                step3: {
                    intro: ' ',
                    img: { src: 'groups003.png', maxWidth: 412, maxHeight: 215 },
                    box: "If this is a cloud inventory, choose a Source and provide credentials.",
                    height: 500
                    },
                step4: {
                    intro: ' ',
                    img: { src: 'groups004.png', maxWidth: 261, maxHeight: 221 },
                    box: "For a cloud inventory, start the sync process by clicking <i class=\"fa fa-exchange\"></i>.",
                    height: 500
                    },
                step5: {
                    intro: "Groups can have subgroups:",
                    img: { src: 'groups005.png', maxWidth: 430, maxHeight: 206 },
                    box: "<div class=\"text-left\">First, select a group. Then click <i class=\"fa fa-plus\"></i> to create a new group. The new group " +
                    "will be added to the selected group.</div>",
                    height: 500
                    },
                step6: {
                    intro: 'Copy or move groups:',
                    img: { src: 'groups006.png', maxWidth: 263, maxHeight: 211 },
                    box: "<div class=\"text-left\">Copy or move a group by dragging and dropping its name onto another group name. A dialog will appear asking " +
                    "if the group should be coppied or moved.</div>",
                    height: 500
                    },
                step7: {
                    intro: 'Next, add hosts:',
                    img: { src: 'groups007.png', maxWidth: 466, maxHeight: 178 },
                    box: "<div class=\"text-left\"><p>First, select a Group. " + 
                    "Then click <i class=\"fa fa-plus\"></i> on the hosts list (the right side of the page) to create a host. " +
                    "The new host will be part of the selected group.</p><p>Note hosts cannot be added to the All Hosts group.</p></div>",
                    height: 500
                    }  
                }  
            }
        });
