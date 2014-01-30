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
                    box: "Click the <i class=\"fa fa-plus\"></i> button to add a new group to the inventory.",
                    autoOffNotice: true,
                    height: 500
                    },
                step2: {
                    img: { src: 'groups002.png', maxWidth: 443, maxHeight: 251 },
                    box: "Provide a name, description and any variables.",
                    height: 460
                    },
                step3: {
                    img: { src: 'groups003.png', maxWidth: 412, maxHeight: 215 },
                    box: "If this a cloud inventory, choose a Source.",
                    height: 460
                    },
                step4: {
                    img: { src: 'groups004.png', maxWidth: 261, maxHeight: 221 },
                    box: "For a cloud inventory, start the sync process by clicking <i class=\"fa fa-exchange\"></i>.",
                    height: 460
                    },
                step5: {
                    intro: "Create subgroups by first clicking a group name to select it.",
                    img: { src: 'groups005.png', maxWidth: 430, maxHeight: 206 },
                    box: "With a group selected, click the <i class=\"fa fa-plus\"></i> to create the new subgroup.",
                    height: 500
                    },
                step6: {
                    intro: ' ',
                    img: { src: 'groups006.png', maxWidth: 263, maxHeight: 211 },
                    box: "Copy or move a group by dragging and dropping the group name.",
                    height: 460
                    }
                }    
            }
        });
