import 'styled-components/macro';
import React, { useContext, useState } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { bool, node, func } from 'prop-types';
import {
  Button,
  WizardContextConsumer,
  WizardFooter,
} from '@patternfly/react-core';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import Wizard from '../../../../../components/Wizard';
import { NodeTypeStep } from './NodeTypeStep';
import RunStep from './RunStep';
import NodeNextButton from './NodeNextButton';

function NodeModal({ askLinkType, i18n, onSave, title }) {
  const history = useHistory();
  const dispatch = useContext(WorkflowDispatchContext);
  const { nodeToEdit } = useContext(WorkflowStateContext);

  let defaultApprovalDescription = '';
  let defaultApprovalName = '';
  let defaultApprovalTimeout = 0;
  let defaultNodeResource = null;
  let defaultNodeType = 'job_template';
  if (nodeToEdit && nodeToEdit.unifiedJobTemplate) {
    if (
      nodeToEdit &&
      nodeToEdit.unifiedJobTemplate &&
      (nodeToEdit.unifiedJobTemplate.type ||
        nodeToEdit.unifiedJobTemplate.unified_job_type)
    ) {
      const ujtType =
        nodeToEdit.unifiedJobTemplate.type ||
        nodeToEdit.unifiedJobTemplate.unified_job_type;
      switch (ujtType) {
        case 'job_template':
        case 'job':
          defaultNodeType = 'job_template';
          defaultNodeResource = nodeToEdit.unifiedJobTemplate;
          break;
        case 'project':
        case 'project_update':
          defaultNodeType = 'project_sync';
          defaultNodeResource = nodeToEdit.unifiedJobTemplate;
          break;
        case 'inventory_source':
        case 'inventory_update':
          defaultNodeType = 'inventory_source_sync';
          defaultNodeResource = nodeToEdit.unifiedJobTemplate;
          break;
        case 'workflow_job_template':
        case 'workflow_job':
          defaultNodeType = 'workflow_job_template';
          defaultNodeResource = nodeToEdit.unifiedJobTemplate;
          break;
        case 'workflow_approval_template':
        case 'workflow_approval':
          defaultNodeType = 'approval';
          defaultApprovalName = nodeToEdit.unifiedJobTemplate.name;
          defaultApprovalDescription =
            nodeToEdit.unifiedJobTemplate.description;
          defaultApprovalTimeout = nodeToEdit.unifiedJobTemplate.timeout;
          break;
        default:
      }
    }
  }
  const [approvalDescription, setApprovalDescription] = useState(
    defaultApprovalDescription
  );
  const [approvalName, setApprovalName] = useState(defaultApprovalName);
  const [approvalTimeout, setApprovalTimeout] = useState(
    defaultApprovalTimeout
  );
  const [linkType, setLinkType] = useState('success');
  const [nodeResource, setNodeResource] = useState(defaultNodeResource);
  const [nodeType, setNodeType] = useState(defaultNodeType);
  const [triggerNext, setTriggerNext] = useState(0);

  const clearQueryParams = () => {
    const parts = history.location.search.replace(/^\?/, '').split('&');
    const otherParts = parts.filter(param =>
      /^!(job_templates\.|projects\.|inventory_sources\.|workflow_job_templates\.)/.test(
        param
      )
    );
    history.replace(`${history.location.pathname}?${otherParts.join('&')}`);
  };

  const handleSaveNode = () => {
    clearQueryParams();

    const resource =
      nodeType === 'approval'
        ? {
            description: approvalDescription,
            name: approvalName,
            timeout: approvalTimeout,
            type: 'workflow_approval_template',
          }
        : nodeResource;

    onSave(resource, askLinkType ? linkType : null);
  };

  const handleCancel = () => {
    clearQueryParams();
    dispatch({ type: 'CANCEL_NODE_MODAL' });
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
              <RunStep linkType={linkType} onUpdateLinkType={setLinkType} />
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
          description={approvalDescription}
          name={approvalName}
          nodeResource={nodeResource}
          nodeType={nodeType}
          onUpdateDescription={setApprovalDescription}
          onUpdateName={setApprovalName}
          onUpdateNodeResource={setNodeResource}
          onUpdateNodeType={handleNodeTypeChange}
          onUpdateTimeout={setApprovalTimeout}
          timeout={approvalTimeout}
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
              <Button id="back-node-modal" variant="secondary" onClick={onBack}>
                {i18n._(t`Back`)}
              </Button>
            )}
            <Button
              id="cancel-node-modal"
              variant="link"
              onClick={handleCancel}
            >
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
      footer={CustomFooter}
      isOpen
      onClose={handleCancel}
      onSave={handleSaveNode}
      steps={steps}
      css="overflow: scroll"
      title={wizardTitle}
    />
  );
}

NodeModal.propTypes = {
  askLinkType: bool.isRequired,
  onSave: func.isRequired,
  title: node.isRequired,
};

export default withI18n()(NodeModal);
