/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventorySummary.js 
 *  Help object for Inventory-> Groups page.
 *
 *  @dict
 */
angular.module('InventorySummaryHelpDefinition', [])
    .value(
    'InventorySummaryHelp', {
        story: {
            hdr: 'Building Your Inventory',
            steps: {
                step1: {
                    intro: 'Start by creating a group:',
                    img: { src: 'help002.png', maxWidth: 460 , maxHeight: 111 },
                    box: "Click the <em>Create New</em> button and add a new group to the inventory.",
                    height: 400
                    },
                step2: {
                    intro: 'After creating a group, add hosts:',
                    img: { src: 'help001.png', maxWidth: 467, maxHeight: 208 },
                    box: "Navigate to <em>Hosts</em> using the drop-down menu, where you can add hosts to the new group",
                    height: 480
                    }
                }    
            }
        });