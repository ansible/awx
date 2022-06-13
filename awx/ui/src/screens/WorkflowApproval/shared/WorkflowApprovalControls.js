import React from 'react';
import { t } from '@lingui/macro';
import {
  Dropdown as PFDropdown,
  DropdownItem,
  Tooltip,
  DropdownToggle,
  DropdownToggleAction,
} from '@patternfly/react-core';
import { CaretDownIcon } from '@patternfly/react-icons';
import { useKebabifiedMenu } from 'contexts/Kebabified';
import styled from 'styled-components';

const Dropdown = styled(PFDropdown)`
  --pf-c-dropdown__toggle--disabled--BackgroundColor: var(
    --pf-global--disabled-color--200
  );

  &&& {
    button {
      color: var(--pf-c-dropdown__toggle--m-primary--Color);
    }
    div.pf-m-disabled > button {
      color: var(--pf-global--disabled-color--100);
    }
  }
`;

function isPending(item) {
  return item.status === 'pending';
}
function isComplete(item) {
  return item.status !== 'pending';
}

function WorkflowApprovalControls({
  selected,
  onHandleDeny,
  onHandleCancel,
  onHandleApprove,
  onHandleToggleToolbarKebab,
  isKebabOpen,
}) {
  const { isKebabified } = useKebabifiedMenu();

  const hasSelectedItems = selected.length > 0;
  const isApproveDenyOrCancelDisabled =
    !hasSelectedItems ||
    !selected.every(
      (item) => item.status === 'pending' && item.can_approve_or_deny
    );

  const renderTooltip = (action) => {
    if (!hasSelectedItems) {
      return t`Select items to approve, deny, or cancel`;
    }
    if (!selected.some(isPending)) {
      return t`Cannot approve, cancel or deny completed workflow approvals`;
    }

    const completedItems = selected
      .filter(isComplete)
      .map((item) => item.name)
      .join(', ');
    if (selected.some(isPending) && selected.some(isComplete)) {
      return t`The following selected items are complete and cannot be acted on: ${completedItems}`;
    }
    return action;
  };

  const dropdownItems = [
    <Tooltip key="deny" content={renderTooltip(t`Deny`)}>
      <div>
        <DropdownItem
          isDisabled={isApproveDenyOrCancelDisabled}
          onClick={onHandleDeny}
          ouiaId="workflow-deny-button"
          description={t`This will continue the workflow along failure and always paths.`}
        >
          {t`Deny`}
        </DropdownItem>
      </div>
    </Tooltip>,
    <Tooltip key="cancel" content={renderTooltip(t`Cancel`)}>
      <div>
        <DropdownItem
          isDisabled={isApproveDenyOrCancelDisabled}
          ouiaId="workflow-cancel-button"
          onClick={onHandleCancel}
          description={t`This will cancel the workflow and no subsequent nodes will execute.`}
        >
          {t`Cancel`}
        </DropdownItem>
      </div>
    </Tooltip>,
  ];
  if (isKebabified) {
    dropdownItems.unshift(
      <Tooltip content={renderTooltip(t`Approve`)}>
        <div>
          <DropdownItem
            isDisabled={isApproveDenyOrCancelDisabled}
            onClick={onHandleApprove}
            ouiaId="workflow-approve-button"
            description={t`This will continue the workflow`}
          >{t`Approve`}</DropdownItem>
        </div>
      </Tooltip>
    );
    return dropdownItems;
  }

  return (
    <Tooltip
      content={renderTooltip(t`Approve, cancel or deny`)}
      key="workflowApproveOrDenyControls"
    >
      <Dropdown
        toggle={
          <DropdownToggle
            isPrimary
            splitButtonVariant="action"
            toggleIndicator={CaretDownIcon}
            splitButtonItems={[
              <DropdownToggleAction
                key="action"
                type="button"
                onClick={onHandleApprove}
              >
                {t`Approve`}
              </DropdownToggleAction>,
            ]}
            data-cy="actions-kebab-toogle"
            isDisabled={isApproveDenyOrCancelDisabled}
            onToggle={onHandleToggleToolbarKebab}
          />
        }
        isOpen={isKebabOpen}
        isPlain
        ouiaId="actions-dropdown"
        dropdownItems={dropdownItems}
      />
    </Tooltip>
  );
}
export default WorkflowApprovalControls;
