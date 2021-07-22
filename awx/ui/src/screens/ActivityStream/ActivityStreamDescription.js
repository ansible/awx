import React from 'react';
import { Link } from 'react-router-dom';
import { t } from '@lingui/macro';

const buildAnchor = (obj, resource, activity) => {
  let url;
  let name;
  // try/except pattern asserts that:
  // if we encounter a case where a UI url can't or
  // shouldn't be generated, just supply the name of the resource
  try {
    // catch-all case to avoid generating urls if a resource has been deleted
    // if a resource still exists, it'll be serialized in the activity's summary_fields
    if (!activity.summary_fields[resource]) {
      throw new Error('The referenced resource no longer exists');
    }
    switch (resource) {
      case 'custom_inventory_script':
        url = `/inventory_scripts/${obj.id}/`;
        break;
      case 'group':
        if (
          activity.operation === 'create' ||
          activity.operation === 'delete'
        ) {
          // the API formats the changes.inventory field as str 'myInventoryName-PrimaryKey'
          const [inventory_id] = activity.changes.inventory
            .split('-')
            .slice(-1);
          url = `/inventories/inventory/${inventory_id}/groups/${activity.changes.id}/details/`;
        } else {
          url = `/inventories/inventory/${
            activity.summary_fields.inventory[0].id
          }/groups/${
            activity.changes.id || activity.changes.object1_pk
          }/details/`;
        }
        break;
      case 'host':
        url = `/hosts/${obj.id}/`;
        break;
      case 'job':
        url = `/jobs/${obj.id}/`;
        break;
      case 'inventory':
        url =
          obj?.kind === 'smart'
            ? `/inventories/smart_inventory/${obj.id}/`
            : `/inventories/inventory/${obj.id}/`;
        break;
      case 'schedule':
        // schedule urls depend on the resource they're associated with
        if (activity.summary_fields.job_template) {
          const jt_id = activity.summary_fields.job_template[0].id;
          url = `/templates/job_template/${jt_id}/schedules/${obj.id}/`;
        } else if (activity.summary_fields.workflow_job_template) {
          const wfjt_id = activity.summary_fields.workflow_job_template[0].id;
          url = `/templates/workflow_job_template/${wfjt_id}/schedules/${obj.id}/`;
        } else if (activity.summary_fields.project) {
          url = `/projects/${activity.summary_fields.project[0].id}/schedules/${obj.id}/`;
        } else if (activity.summary_fields.system_job_template) {
          url = null;
        } else {
          // urls for inventory sync schedules currently depend on having
          // an inventory id and group id
          throw new Error(
            'activity.summary_fields to build this url not implemented yet'
          );
        }
        break;
      case 'setting':
        url = `/settings/`;
        break;
      case 'notification_template':
        url = `/notification_templates/${obj.id}/`;
        break;
      case 'role':
        throw new Error(
          'role object management is not consolidated to a single UI view'
        );
      case 'job_template':
        url = `/templates/job_template/${obj.id}/`;
        break;
      case 'workflow_job_template':
        url = `/templates/workflow_job_template/${obj.id}/`;
        break;
      case 'workflow_job_template_node': {
        const { id: wfjt_id, name: wfjt_name } =
          activity.summary_fields.workflow_job_template[0];
        url = `/templates/workflow_job_template/${wfjt_id}/`;
        name = wfjt_name;
        break;
      }
      case 'workflow_job':
        url = `/jobs/workflow/${obj.id}/`;
        break;
      case 'label':
        url = null;
        break;
      case 'inventory_source': {
        const inventoryId = (obj.inventory || '').split('-').reverse()[0];
        url = `/inventories/inventory/${inventoryId}/sources/${obj.id}/details/`;
        break;
      }
      case 'o_auth2_application':
        url = `/applications/${obj.id}/`;
        break;
      case 'workflow_approval':
        url = `/jobs/workflow/${activity.summary_fields.workflow_job[0].id}/output/`;
        name = `${activity.summary_fields.workflow_job[0].name} | ${activity.summary_fields.workflow_approval[0].name}`;
        break;
      case 'workflow_approval_template':
        url = `/templates/workflow_job_template/${activity.summary_fields.workflow_job_template[0].id}/visualizer/`;
        name = `${activity.summary_fields.workflow_job_template[0].name} | ${activity.summary_fields.workflow_approval_template[0].name}`;
        break;
      default:
        url = `/${resource}s/${obj.id}/`;
    }

    name = name || obj.name || obj.username;

    if (url) {
      return <Link to={url}>{name}</Link>;
    }

    return <span>{name}</span>;
  } catch (err) {
    return <span>{obj.name || obj.username || ''}</span>;
  }
};

const getPastTense = (item) => (/e$/.test(item) ? `${item}d` : `${item}ed`);

const isGroupRelationship = (item) =>
  item.object1 === 'group' &&
  item.object2 === 'group' &&
  item.summary_fields.group.length > 1;

const buildLabeledLink = (label, link) => (
  <span>
    {label} {link}
  </span>
);

function ActivityStreamDescription({ activity }) {
  const labeledLinks = [];
  // Activity stream objects will outlive the resources they reference
  // in that case, summary_fields will not be available - show generic error text instead
  try {
    switch (activity.object_association) {
      // explicit role dis+associations
      case 'role': {
        let { object1, object2 } = activity;

        // if object1 winds up being the role's resource, we need to swap the objects
        // in order to make the sentence make sense.
        if (activity.object_type === object1) {
          object1 = activity.object2;
          object2 = activity.object1;
        }

        // object1 field is resource targeted by the dis+association
        // object2 field is the resource the role is inherited from
        // summary_field.role[0] contains ref info about the role
        switch (activity.operation) {
          // expected outcome: "disassociated <object2> role_name from <object1>"
          case 'disassociate':
            if (isGroupRelationship(activity)) {
              labeledLinks.push(
                buildLabeledLink(
                  getPastTense(activity.operation),
                  buildAnchor(
                    activity.summary_fields.group[1],
                    object2,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `${activity.summary_fields.role[0].role_field} from`,
                  buildAnchor(
                    activity.summary_fields.group[0],
                    object1,
                    activity
                  )
                )
              );
            } else {
              labeledLinks.push(
                buildLabeledLink(
                  getPastTense(activity.operation),
                  buildAnchor(
                    activity.summary_fields[object2][0],
                    object2,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `${activity.summary_fields.role[0].role_field} from`,
                  buildAnchor(
                    activity.summary_fields[object1][0],
                    object1,
                    activity
                  )
                )
              );
            }
            break;
          // expected outcome: "associated <object2> role_name to <object1>"
          case 'associate':
            if (isGroupRelationship(activity)) {
              labeledLinks.push(
                buildLabeledLink(
                  getPastTense(activity.operation),
                  buildAnchor(
                    activity.summary_fields.group[1],
                    object2,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `${activity.summary_fields.role[0].role_field} to`,
                  buildAnchor(
                    activity.summary_fields.group[0],
                    object1,
                    activity
                  )
                )
              );
            } else {
              labeledLinks.push(
                buildLabeledLink(
                  getPastTense(activity.operation),
                  buildAnchor(
                    activity.summary_fields[object2][0],
                    object2,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `${activity.summary_fields.role[0].role_field} to`,
                  buildAnchor(
                    activity.summary_fields[object1][0],
                    object1,
                    activity
                  )
                )
              );
            }
            break;
          default:
            break;
        }
        break;
        // inherited role dis+associations (logic identical to case 'role')
      }
      case 'parents':
        // object1 field is resource targeted by the dis+association
        // object2 field is the resource the role is inherited from
        // summary_field.role[0] contains ref info about the role
        switch (activity.operation) {
          // expected outcome: "disassociated <object2> role_name from <object1>"
          case 'disassociate':
            if (isGroupRelationship(activity)) {
              labeledLinks.push(
                buildLabeledLink(
                  `${getPastTense(activity.operation)} ${activity.object2}`,
                  buildAnchor(
                    activity.summary_fields.group[1],
                    activity.object2,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `from ${activity.object1}`,
                  buildAnchor(
                    activity.summary_fields.group[0],
                    activity.object1,
                    activity
                  )
                )
              );
            } else {
              labeledLinks.push(
                buildLabeledLink(
                  getPastTense(activity.operation),
                  buildAnchor(
                    activity.summary_fields[activity.object2][0],
                    activity.object2,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `${activity.summary_fields.role[0].role_field} from`,
                  buildAnchor(
                    activity.summary_fields[activity.object1][0],
                    activity.object1,
                    activity
                  )
                )
              );
            }
            break;
          // expected outcome: "associated <object2> role_name to <object1>"
          case 'associate':
            if (isGroupRelationship(activity)) {
              labeledLinks.push(
                buildLabeledLink(
                  `${getPastTense(activity.operation)} ${activity.object1}`,
                  buildAnchor(
                    activity.summary_fields.group[0],
                    activity.object1,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `to ${activity.object2}`,
                  buildAnchor(
                    activity.summary_fields.group[1],
                    activity.object2,
                    activity
                  )
                )
              );
            } else {
              labeledLinks.push(
                buildLabeledLink(
                  getPastTense(activity.operation),
                  buildAnchor(
                    activity.summary_fields[activity.object2][0],
                    activity.object2,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `${activity.summary_fields.role[0].role_field} to`,
                  buildAnchor(
                    activity.summary_fields[activity.object1][0],
                    activity.object1,
                    activity
                  )
                )
              );
            }
            break;
          default:
            break;
        }
        break;
      // CRUD operations / resource on resource dis+associations
      default:
        switch (activity.operation) {
          // expected outcome: "disassociated <object2> from <object1>"
          case 'disassociate':
            if (isGroupRelationship(activity)) {
              labeledLinks.push(
                buildLabeledLink(
                  `${getPastTense(activity.operation)} ${activity.object2}`,
                  buildAnchor(
                    activity.summary_fields.group[1],
                    activity.object2,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `from ${activity.object1}`,
                  buildAnchor(
                    activity.summary_fields.group[0],
                    activity.object1,
                    activity
                  )
                )
              );
            } else if (
              activity.object1 === 'workflow_job_template_node' &&
              activity.object2 === 'workflow_job_template_node'
            ) {
              labeledLinks.push(
                buildLabeledLink(
                  `${getPastTense(activity.operation)} two nodes on workflow`,
                  buildAnchor(
                    activity.summary_fields[activity.object1[0]],
                    activity.object1,
                    activity
                  )
                )
              );
            } else {
              labeledLinks.push(
                buildLabeledLink(
                  `${getPastTense(activity.operation)} ${activity.object2}`,
                  buildAnchor(
                    activity.summary_fields[activity.object2][0],
                    activity.object2,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `from ${activity.object1}`,
                  buildAnchor(
                    activity.summary_fields[activity.object1][0],
                    activity.object1,
                    activity
                  )
                )
              );
            }
            break;
          // expected outcome "associated <object2> to <object1>"
          case 'associate':
            // groups are the only resource that can be associated/disassociated into each other
            if (isGroupRelationship(activity)) {
              labeledLinks.push(
                buildLabeledLink(
                  `${getPastTense(activity.operation)} ${activity.object1}`,
                  buildAnchor(
                    activity.summary_fields.group[0],
                    activity.object1,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `to ${activity.object2}`,
                  buildAnchor(
                    activity.summary_fields.group[1],
                    activity.object2,
                    activity
                  )
                )
              );
            } else if (
              activity.object1 === 'workflow_job_template_node' &&
              activity.object2 === 'workflow_job_template_node'
            ) {
              labeledLinks.push(
                buildLabeledLink(
                  `${getPastTense(activity.operation)} two nodes on workflow`,
                  buildAnchor(
                    activity.summary_fields[activity.object1[0]],
                    activity.object1,
                    activity
                  )
                )
              );
            } else {
              labeledLinks.push(
                buildLabeledLink(
                  `${getPastTense(activity.operation)} ${activity.object1}`,
                  buildAnchor(
                    activity.summary_fields[activity.object1][0],
                    activity.object1,
                    activity
                  )
                )
              );
              labeledLinks.push(
                buildLabeledLink(
                  `to ${activity.object2}`,
                  buildAnchor(
                    activity.summary_fields[activity.object2][0],
                    activity.object2,
                    activity
                  )
                )
              );
            }
            break;
          case 'delete':
            labeledLinks.push(
              buildLabeledLink(
                `${getPastTense(activity.operation)} ${activity.object1}`,
                buildAnchor(activity.changes, activity.object1, activity)
              )
            );
            break;
          // expected outcome: "operation <object1>"
          case 'update':
            if (
              activity.object1 === 'workflow_approval' &&
              activity?.changes?.status?.length === 2
            ) {
              let operationText = '';
              if (activity.changes.status[1] === 'successful') {
                operationText = t`approved`;
              } else if (activity.changes.status[1] === 'failed') {
                if (
                  activity.changes.timed_out &&
                  activity.changes.timed_out[1] === true
                ) {
                  operationText = t`timed out`;
                } else {
                  operationText = t`denied`;
                }
              } else {
                operationText = t`updated`;
              }
              labeledLinks.push(
                buildLabeledLink(
                  `${operationText} ${activity.object1}`,
                  buildAnchor(
                    activity.summary_fields[activity.object1][0],
                    activity.object1,
                    activity
                  )
                )
              );
            } else {
              labeledLinks.push(
                buildLabeledLink(
                  `${getPastTense(activity.operation)} ${activity.object1}`,
                  buildAnchor(
                    activity.summary_fields[activity.object1][0],
                    activity.object1,
                    activity
                  )
                )
              );
            }
            break;
          case 'create':
            labeledLinks.push(
              buildLabeledLink(
                `${getPastTense(activity.operation)} ${activity.object1}`,
                buildAnchor(activity.changes, activity.object1, activity)
              )
            );
            break;
          default:
            break;
        }
        break;
    }
  } catch (err) {
    return <span>{t`Event summary not available`}</span>;
  }

  return (
    <span>
      {labeledLinks.reduce(
        (acc, x) =>
          acc === null ? (
            x
          ) : (
            <>
              {acc} {x}
            </>
          ),
        null
      )}
    </span>
  );
}

export default ActivityStreamDescription;
