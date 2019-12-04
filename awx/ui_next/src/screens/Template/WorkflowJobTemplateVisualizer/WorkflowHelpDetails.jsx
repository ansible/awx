import React, { Fragment } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';

const GridDL = styled.dl`
  display: grid;
  grid-template-columns: max-content;
  column-gap: 15px;
  row-gap: 0px;

  dt {
    grid-column-start: 1;
  }

  dd {
    grid-column-start: 2;
  }
`;

function WorkflowHelpDetails({ d, i18n }) {
  const rows = [];

  if (d.type === 'link') {
    let linkType;
    switch (d.edgeType) {
      case 'always':
        linkType = i18n._(t`Always`);
        break;
      case 'success':
        linkType = i18n._(t`On Success`);
        break;
      case 'failure':
        linkType = i18n._(t`On Failure`);
        break;
      default:
        linkType = '';
    }

    rows.push({
      label: i18n._(t`Run`),
      value: linkType,
    });
  } else if (d.type === 'node') {
    if (d.unifiedJobTemplate) {
      rows.push({
        label: i18n._(t`Name`),
        value: d.unifiedJobTemplate.name,
      });

      let nodeType;
      switch (d.unifiedJobTemplate.unified_job_type) {
        case 'job':
          nodeType = i18n._(t`Job Template`);
          break;
        case 'workflow_job':
          nodeType = i18n._(t`Workflow Job Template`);
          break;
        case 'project_update':
          nodeType = i18n._(t`Project Update`);
          break;
        case 'inventory_update':
          nodeType = i18n._(t`Inventory Update`);
          break;
        case 'workflow_approval':
          nodeType = i18n._(t`Workflow Approval`);
          break;
        default:
          nodeType = '';
      }

      rows.push({
        label: i18n._(t`Type`),
        value: nodeType,
      });
    } else {
      // todo: this scenario (deleted)
    }
  }

  return (
    <GridDL>
      {rows.map(row => (
        <Fragment key={row.label}>
          <dt>
            <b>{row.label}</b>
          </dt>
          <dd>{row.value}</dd>
        </Fragment>
      ))}
    </GridDL>
  );
}

export default withI18n()(WorkflowHelpDetails);
