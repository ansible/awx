import React from 'react';
import { Modal } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import ApprovalDetails from './ApprovalDetails';
import InventorySourceSyncDetails from './InventorySourceSyncDetails';
import JobTemplateDetails from './JobTemplateDetails';
import ProjectSyncDetails from './ProjectSyncDetails';
import WorkflowJobTemplateDetails from './WorkflowJobTemplateDetails';

function NodeViewModal({ i18n, onClose, node }) {
  return (
    <Modal
      isLarge
      isOpen={true}
      title={i18n._(t`Node Details | ${node.unifiedJobTemplate.name}`)}
      onClose={onClose}
    >
      {(node.unifiedJobTemplate.type === 'job_template' || node.unifiedJobTemplate.unified_job_type === 'job') && (
        <JobTemplateDetails node={node} />
      )}
      {(node.unifiedJobTemplate.type === 'workflow_approval_template' || node.unifiedJobTemplate.unified_job_type) === 'workflow_approval' && (
        <ApprovalDetails node={node} />
      )}
      {(node.unifiedJobTemplate.type === 'project' || node.unifiedJobTemplate.unified_job_type === 'project_update') && (
        <ProjectSyncDetails node={node} />
      )}
      {(node.unifiedJobTemplate.type === 'inventory_source' || node.unifiedJobTemplate.unified_job_type === 'inventory_update') && (
        <InventorySourceSyncDetails node={node} />
      )}
      {(node.unifiedJobTemplate.type === 'workflow_job_template' || node.unifiedJobTemplate.unified_job_type === 'workflow_job') && (
        <WorkflowJobTemplateDetails node={node} />
      )}
    </Modal>
  );
}

export default withI18n()(NodeViewModal);
