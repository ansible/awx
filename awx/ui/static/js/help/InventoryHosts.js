/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventoryHosts.js 
 *  Help object for Inventory-> Hosts page.
 *
 *  
 */
angular.module('InventoryHostsHelpDefinition', [])
    .value(
    'InventoryHostsHelp', {
        story: {
            hdr: 'Managing Hosts',
            steps: {
                step1: {
                    intro: 'Start by selecting a group:',
                    img: { src: 'help003.png', maxWidth: 315 , maxHeight: 198 },
                    box: "On the group selector, click the name of a group. Hosts contained in the group" +
                        " will appear on the right.",
                    height: 500
                    }
                }    
            }
        });