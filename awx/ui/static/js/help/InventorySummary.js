/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
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
            hdr: 'Getting Started',
            steps: {
                step1: {
                    intro: 'Start by creating a group:',
                    img: 'help002.png',
                    box: "Click the <em>Create New</em> button and add a new group to the inventory.",
                    height: 400
                    },
                step2: {
                    intro: 'After creating a group, add hosts:',
                    img: 'help001.png',
                    box: "Navigate to <em>Hosts</em> using the drop-down menu, where you can add hosts to the new group",
                    height: 480
                    }
                }    
            }
        });