export default
    function JobsListUpdate() {
        return function(params) {
            var scope = params.scope,
                parent_scope = params.parent_scope,
                list = params.list;

            scope[list.name].forEach(function(item, item_idx) {
                var fld, field,
                    itm = scope[list.name][item_idx];

                //if (item.type === 'inventory_update') {
                //    itm.name = itm.name.replace(/^.*?:/,'').replace(/^: /,'');
                //}

                // Set the item type label
                if (list.fields.type) {
                    parent_scope.type_choices.forEach(function(choice) {
                        if (choice.value === item.type) {
                            itm.type_label = choice.label;
                        }
                    });
                }
                // Set the job status label
                parent_scope.status_choices.forEach(function(status) {
                    if (status.value === item.status) {
                        itm.status_label = status.label;
                    }
                });

                if (list.name === 'completed_jobs' || list.name === 'running_jobs') {
                    itm.status_tip = itm.status_label + '. Click for details.';
                }
                else if (list.name === 'queued_jobs') {
                    itm.status_tip = 'Pending';
                }

                // Copy summary_field values
                for (field in list.fields) {
                    fld = list.fields[field];
                    if (fld.sourceModel) {
                        if (itm.summary_fields[fld.sourceModel]) {
                            itm[field] = itm.summary_fields[fld.sourceModel][fld.sourceField];
                        }
                    }
                }
            });
        };
    }
