import React, { useContext } from 'react';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import { KebabifiedContext } from 'contexts/Kebabified';
import { WorkflowApproval } from 'types';

function cannotDeny(item) {
  return !item.can_approve_or_deny;
}

function WorkflowApprovalListDenyButton({ onDeny, selectedItems }) {
  const { isKebabified } = useContext(KebabifiedContext);

  const renderTooltip = () => {
    if (selectedItems.length === 0) {
      return t`Select a row to deny`;
    }

    const itemsUnableToDeny = selectedItems
      .filter(cannotDeny)
      .map((item) => item.name)
      .join(', ');

    if (selectedItems.some(cannotDeny)) {
      return t`You are unable to act on the following workflow approvals: ${itemsUnableToDeny}`;
    }

    return t`Deny`;
  };

  const isDisabled =
    selectedItems.length === 0 || selectedItems.some(cannotDeny);

  return (
    /* eslint-disable-next-line react/jsx-no-useless-fragment */
    <>
      {isKebabified ? (
        <DropdownItem
          key="deny"
          isDisabled={isDisabled}
          component="button"
          onClick={onDeny}
        >
          {t`Deny`}
        </DropdownItem>
      ) : (
        <Tooltip content={renderTooltip()} position="top">
          <div>
            <Button
              ouiaId="workflow-approval-deny-button"
              isDisabled={isDisabled}
              aria-label={t`Deny`}
              variant="danger"
              onClick={onDeny}
            >
              {t`Deny`}
            </Button>
          </div>
        </Tooltip>
      )}
    </>
  );
}

WorkflowApprovalListDenyButton.propTypes = {
  onDeny: PropTypes.func.isRequired,
  selectedItems: PropTypes.arrayOf(WorkflowApproval),
};

WorkflowApprovalListDenyButton.defaultProps = {
  selectedItems: [],
};

export default WorkflowApprovalListDenyButton;
