/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [ () => {
    var val = {
        filter: function(str, reports_dataset){
            let filteredSet;
            if(str === "total"){
                filteredSet = reports_dataset;
            }
            if(str === "solvable"){
                filteredSet = _.filter(reports_dataset, (report)=>{return (report.maintenance_actions.length > 0);});
            }
            if(str === "not_solvable"){
                filteredSet = _.filter(reports_dataset, (report)=>{return (report.maintenance_actions.length === 0);});
            }
            if(str === "critical"){
                filteredSet = _.filter(reports_dataset, (report)=>{return (report.rule.severity === 'CRITICAL');});
            }
            if(str === "high"){
                filteredSet = _.filter(reports_dataset, (report)=>{return (report.rule.severity === 'ERROR');});
            }
            if(str === "medium"){
                filteredSet = _.filter(reports_dataset, (report)=>{return (report.rule.severity === 'WARN');});
            }
            if(str === "low"){
                filteredSet = _.filter(reports_dataset, (report)=>{return (report.rule.severity === 'INFO');});
            }
            return filteredSet;
        }
    };
    return val;
}];
