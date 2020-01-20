import React, { Fragment } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { shape } from 'prop-types';
import { secondsToHHMMSS } from '@util/dates';

const GridDL = styled.dl`
  column-gap: 15px;
  display: grid;
  grid-template-columns: max-content;
  row-gap: 0px;
  dt {
    grid-column-start: 1;
  }
  dd {
    grid-column-start: 2;
  }
`;

function WorkflowNodeHelp({ node, i18n }) {
  let nodeType;
  if (node.unifiedJobTemplate) {
    const type =
      node.unifiedJobTemplate.unified_job_type || node.unifiedJobTemplate.type;
    switch (type) {
      case 'job_template':
      case 'job':
        nodeType = i18n._(t`Job Template`);
        break;
      case 'workflow_job_template':
      case 'workflow_job':
        nodeType = i18n._(t`Workflow Job Template`);
        break;
      case 'project':
      case 'project_update':
        nodeType = i18n._(t`Project Update`);
        break;
      case 'inventory_source':
      case 'inventory_update':
        nodeType = i18n._(t`Inventory Update`);
        break;
      case 'workflow_approval_template':
      case 'workflow_approval':
        nodeType = i18n._(t`Workflow Approval`);
        break;
      default:
        nodeType = '';
    }
  }

  let jobStatus;
  if (node.job) {
    switch (node.job.status) {
      case 'new':
        jobStatus = i18n._(t`New`);
        break;
      case 'pending':
        jobStatus = i18n._(t`Pending`);
        break;
      case 'waiting':
        jobStatus = i18n._(t`Waiting`);
        break;
      case 'running':
        jobStatus = i18n._(t`Running`);
        break;
      case 'successful':
        jobStatus = i18n._(t`Successful`);
        break;
      case 'failed':
        jobStatus = i18n._(t`Failed`);
        break;
      case 'error':
        jobStatus = i18n._(t`Error`);
        break;
      case 'canceled':
        jobStatus = i18n._(t`Canceled`);
        break;
      case 'never updated':
        jobStatus = i18n._(t`Never Updated`);
        break;
      case 'ok':
        jobStatus = i18n._(t`OK`);
        break;
      case 'missing':
        jobStatus = i18n._(t`Missing`);
        break;
      case 'none':
        jobStatus = i18n._(t`None`);
        break;
      case 'updating':
        jobStatus = i18n._(t`Updating`);
        break;
      default:
        jobStatus = '';
    }
  }

  return (
    <Fragment>
      <GridDL>
        {node.unifiedJobTemplate && (
          <Fragment>
            <dt>
              <b>{i18n._(t`Name`)}</b>
            </dt>
            <dd>{node.unifiedJobTemplate.name}</dd>
            <dt>
              <b>{i18n._(t`Type`)}</b>
            </dt>
            <dd>{nodeType}</dd>
          </Fragment>
        )}
        {node.job && (
          <Fragment>
            <dt>
              <b>{i18n._(t`Job Status`)}</b>
            </dt>
            <dd>{jobStatus}</dd>
            {node.job.elapsed && (
              <Fragment>
                <dt>
                  <b>{i18n._(t`Elapsed`)}</b>
                </dt>
                <dd>{secondsToHHMMSS(node.job.elapsed)}</dd>
              </Fragment>
            )}
          </Fragment>
        )}
      </GridDL>
      {node.job && (
        <p css="margin-top: 10px">{i18n._(t`Click to view job details`)}</p>
      )}
    </Fragment>
  );
}

WorkflowNodeHelp.propTypes = {
  node: shape().isRequired,
};

export default withI18n()(WorkflowNodeHelp);
