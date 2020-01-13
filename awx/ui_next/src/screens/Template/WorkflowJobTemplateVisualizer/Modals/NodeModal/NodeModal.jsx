import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  Wizard,
  WizardContextConsumer,
  WizardFooter,
} from '@patternfly/react-core';
import NodeResourceStep from './NodeResourceStep';
import NodeTypeStep from './NodeTypeStep';
import NodeNextButton from './NodeNextButton';
import NodeApprovalStep from './NodeApprovalStep';
import ApprovalPreviewStep from './ApprovalPreviewStep';
import JobTemplatePreviewStep from './JobTemplatePreviewStep';
import InventorySyncPreviewStep from './InventorySyncPreviewStep';
import ProjectSyncPreviewStep from './ProjectSyncPreviewStep';
import WorkflowJobTemplatePreviewStep from './WorkflowJobTemplatePreviewStep';

import {
  JobTemplatesAPI,
  ProjectsAPI,
  InventorySourcesAPI,
  WorkflowJobTemplatesAPI,
} from '@api';

const readInventorySources = async queryParams =>
  InventorySourcesAPI.read(queryParams);
const readJobTemplates = async queryParams =>
  JobTemplatesAPI.read(queryParams, { role_level: 'execute_role' });
const readProjects = async queryParams => ProjectsAPI.read(queryParams);
const readWorkflowJobTemplates = async queryParams =>
  WorkflowJobTemplatesAPI.read(queryParams, { role_level: 'execute_role' });

function NodeModal({ i18n, title, onClose, onSave, node, askLinkType }) {
  let defaultNodeType = 'job_template';
  let defaultNodeResource = null;
  let defaultApprovalName = '';
  let defaultApprovalDescription = '';
  let defaultApprovalTimeout = 0;
  if (node && node.unifiedJobTemplate) {
    if (
      node &&
      node.unifiedJobTemplate &&
      (node.unifiedJobTemplate.type || node.unifiedJobTemplate.unified_job_type)
    ) {
      const ujtType =
        node.unifiedJobTemplate.type ||
        node.unifiedJobTemplate.unified_job_type;
      switch (ujtType) {
        case 'job_template':
        case 'job':
          defaultNodeType = 'job_template';
          defaultNodeResource = node.unifiedJobTemplate;
          break;
        case 'project':
        case 'project_update':
          defaultNodeType = 'project_sync';
          defaultNodeResource = node.unifiedJobTemplate;
          break;
        case 'inventory_source':
        case 'inventory_update':
          defaultNodeType = 'inventory_source_sync';
          defaultNodeResource = node.unifiedJobTemplate;
          break;
        case 'workflow_job_template':
        case 'workflow_job':
          defaultNodeType = 'workflow_job_template';
          defaultNodeResource = node.unifiedJobTemplate;
          break;
        case 'workflow_approval_template':
        case 'workflow_approval':
          defaultNodeType = 'approval';
          defaultApprovalName = node.unifiedJobTemplate.name;
          defaultApprovalDescription = node.unifiedJobTemplate.description;
          defaultApprovalTimeout = node.unifiedJobTemplate.timeout;
          break;
        default:
      }
    }
  }
  const [nodeType, setNodeType] = useState(defaultNodeType);
  const [linkType, setLinkType] = useState('success');
  const [nodeResource, setNodeResource] = useState(defaultNodeResource);
  const [showApprovalStep, setShowApprovalStep] = useState(
    defaultNodeType === 'approval'
  );
  const [showResourceStep, setShowResourceStep] = useState(
    defaultNodeResource ? true : false
  );
  const [showPreviewStep, setShowPreviewStep] = useState(
    defaultNodeType === 'approval' || defaultNodeResource ? true : false
  );
  const [triggerNext, setTriggerNext] = useState(0);
  const [approvalName, setApprovalName] = useState(defaultApprovalName);
  const [approvalDescription, setApprovalDescription] = useState(
    defaultApprovalDescription
  );
  const [approvalTimeout, setApprovalTimeout] = useState(
    defaultApprovalTimeout
  );

  const handleSaveNode = () => {
    const resource =
      nodeType === 'approval'
        ? {
            name: approvalName,
            description: approvalDescription,
            timeout: approvalTimeout,
            type: 'workflow_approval_template',
          }
        : nodeResource;

    // TODO: pick edgeType or linkType and be consistent across all files.

    onSave({
      nodeType,
      edgeType: linkType,
      nodeResource: resource,
    });
  };

  const resourceSearch = queryParams => {
    switch (nodeType) {
      case 'inventory_source_sync':
        return readInventorySources(queryParams);
      case 'job_template':
        return readJobTemplates(queryParams);
      case 'project_sync':
        return readProjects(queryParams);
      case 'workflow_job_template':
        return readWorkflowJobTemplates(queryParams);
      default:
        throw new Error(i18n._(t`Missing node type`));
    }
  };

  const handleNextClick = activeStep => {
    if (activeStep.key === 'node_type') {
      if (
        [
          'inventory_source_sync',
          'job_template',
          'project_sync',
          'workflow_job_template',
        ].includes(nodeType)
      ) {
        setShowApprovalStep(false);
        setShowResourceStep(true);
      } else if (nodeType === 'approval') {
        setShowResourceStep(false);
        setShowApprovalStep(true);
      }
      setShowPreviewStep(true);
    }
    setTriggerNext(triggerNext + 1);
  };

  const handleNodeTypeChange = newNodeType => {
    setNodeType(newNodeType);
    setShowResourceStep(false);
    setShowApprovalStep(false);
    setShowPreviewStep(false);
    setNodeResource(null);
    setApprovalName('');
    setApprovalDescription('');
    setApprovalTimeout(0);
  };

  const steps = [
    {
      name: node ? i18n._(t`Node Type`) : i18n._(t`Run/Node Type`),
      key: 'node_type',
      component: (
        <NodeTypeStep
          nodeType={nodeType}
          updateNodeType={handleNodeTypeChange}
          askLinkType={askLinkType}
          linkType={linkType}
          updateLinkType={setLinkType}
        />
      ),
      enableNext: nodeType !== null,
    },
    ...(showResourceStep
      ? [
          {
            name: i18n._(t`Select Node Resource`),
            key: 'node_resource',
            enableNext: nodeResource !== null,
            component: (
              <NodeResourceStep
                nodeType={nodeType}
                search={resourceSearch}
                nodeResource={nodeResource}
                updateNodeResource={setNodeResource}
              />
            ),
          },
        ]
      : []),
    ...(showApprovalStep
      ? [
          {
            name: i18n._(t`Configure Approval`),
            key: 'approval',
            component: (
              <NodeApprovalStep
                name={approvalName}
                updateName={setApprovalName}
                description={approvalDescription}
                updateDescription={setApprovalDescription}
                timeout={approvalTimeout}
                updateTimeout={setApprovalTimeout}
              />
            ),
            enableNext: approvalName !== '',
          },
        ]
      : []),
    ...(showPreviewStep
      ? [
          {
            name: i18n._(t`Preview`),
            key: 'preview',
            component: (
              <>
                {nodeType === 'approval' && (
                  <ApprovalPreviewStep
                    name={approvalName}
                    description={approvalDescription}
                    timeout={approvalTimeout}
                    linkType={linkType}
                  />
                )}
                {nodeType === 'job_template' && (
                  <JobTemplatePreviewStep
                    jobTemplate={nodeResource}
                    linkType={linkType}
                  />
                )}
                {nodeType === 'inventory_source_sync' && (
                  <InventorySyncPreviewStep
                    inventorySource={nodeResource}
                    linkType={linkType}
                  />
                )}
                {nodeType === 'project_sync' && (
                  <ProjectSyncPreviewStep
                    project={nodeResource}
                    linkType={linkType}
                  />
                )}
                {nodeType === 'workflow_job_template' && (
                  <WorkflowJobTemplatePreviewStep
                    workflowJobTemplate={nodeResource}
                    linkType={linkType}
                  />
                )}
              </>
            ),
            enableNext: true,
          },
        ]
      : []),
  ];

  steps.forEach((step, n) => {
    step.id = n + 1;
  });

  const CustomFooter = (
    <WizardFooter>
      <WizardContextConsumer>
        {({ activeStep, onNext, onBack, onClose }) => (
          <>
            <NodeNextButton
              triggerNext={triggerNext}
              activeStep={activeStep}
              onNext={onNext}
              onClick={handleNextClick}
            />
            {activeStep && activeStep.id !== 1 && (
              <Button variant="secondary" onClick={onBack}>
                {i18n._(t`Back`)}
              </Button>
            )}
            <Button variant="link" onClick={onClose}>
              {i18n._(t`Cancel`)}
            </Button>
          </>
        )}
      </WizardContextConsumer>
    </WizardFooter>
  );

  return (
    <Wizard
      style={{ overflow: 'scroll' }}
      isOpen
      steps={steps}
      title={title}
      onClose={onClose}
      onSave={handleSaveNode}
      footer={CustomFooter}
    />
  );
}

export default withI18n()(NodeModal);
