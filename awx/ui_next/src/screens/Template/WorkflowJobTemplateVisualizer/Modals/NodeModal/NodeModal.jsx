import React, { useState } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  WizardContextConsumer,
  WizardFooter,
} from '@patternfly/react-core';
import NodeTypeStep from './NodeTypeStep/NodeTypeStep';
import RunStep from './RunStep';
import NodeNextButton from './NodeNextButton';
import { Wizard } from '@components/Wizard';

function NodeModal({
  history,
  i18n,
  title,
  onClose,
  onSave,
  node,
  askLinkType,
}) {
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
  const [triggerNext, setTriggerNext] = useState(0);
  const [approvalName, setApprovalName] = useState(defaultApprovalName);
  const [approvalDescription, setApprovalDescription] = useState(
    defaultApprovalDescription
  );
  const [approvalTimeout, setApprovalTimeout] = useState(
    defaultApprovalTimeout
  );

  const clearQueryParams = () => {
    const parts = history.location.search.replace(/^\?/, '').split('&');
    const otherParts = parts.filter(param =>
      /^!(job_templates\.|projects\.|inventory_sources\.|workflow_job_templates\.)/.test(
        param
      )
    );
    history.push(`${history.location.pathname}?${otherParts.join('&')}`);
  };

  const handleSaveNode = () => {
    clearQueryParams();

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

  const handleCancel = () => {
    clearQueryParams();
    onClose();
  };

  const handleNodeTypeChange = newNodeType => {
    setNodeType(newNodeType);
    setNodeResource(null);
    setApprovalName('');
    setApprovalDescription('');
    setApprovalTimeout(0);
  };

  const steps = [
    ...(askLinkType
      ? [
          {
            name: i18n._(t`Run Type`),
            key: 'run_type',
            component: (
              <RunStep linkType={linkType} updateLinkType={setLinkType} />
            ),
            enableNext: linkType !== null,
          },
        ]
      : []),
    {
      name: i18n._(t`Node Type`),
      key: 'node_resource',
      enableNext:
        (nodeType !== 'approval' && nodeResource !== null) ||
        (nodeType === 'approval' && approvalName !== ''),
      component: (
        <NodeTypeStep
          nodeType={nodeType}
          updateNodeType={handleNodeTypeChange}
          nodeResource={nodeResource}
          updateNodeResource={setNodeResource}
          name={approvalName}
          updateName={setApprovalName}
          description={approvalDescription}
          updateDescription={setApprovalDescription}
          timeout={approvalTimeout}
          updateTimeout={setApprovalTimeout}
        />
      ),
    },
  ];

  steps.forEach((step, n) => {
    step.id = n + 1;
  });

  const CustomFooter = (
    <WizardFooter>
      <WizardContextConsumer>
        {({ activeStep, onNext, onBack }) => (
          <>
            <NodeNextButton
              triggerNext={triggerNext}
              activeStep={activeStep}
              onNext={onNext}
              onClick={() => setTriggerNext(triggerNext + 1)}
              buttonText={
                activeStep.key === 'node_resource'
                  ? i18n._(t`Save`)
                  : i18n._(t`Next`)
              }
            />
            {activeStep && activeStep.id !== 1 && (
              <Button variant="secondary" onClick={onBack}>
                {i18n._(t`Back`)}
              </Button>
            )}
            <Button variant="link" onClick={handleCancel}>
              {i18n._(t`Cancel`)}
            </Button>
          </>
        )}
      </WizardContextConsumer>
    </WizardFooter>
  );

  const wizardTitle = nodeResource ? `${title} | ${nodeResource.name}` : title;

  return (
    <Wizard
      style={{ overflow: 'scroll' }}
      isOpen
      steps={steps}
      title={wizardTitle}
      onClose={handleCancel}
      onSave={handleSaveNode}
      footer={CustomFooter}
    />
  );
}

export default withI18n()(withRouter(NodeModal));
