import React, { useContext } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import { KebabifiedContext } from '../../../contexts/Kebabified';
import { WorkflowApproval } from '../../../types';

function cannotApprove(item) {
  return !item.can_approve_or_deny;
}

function WorkflowApprovalListApproveButton({ onApprove, selectedItems, i18n }) {
  const { isKebabified } = useContext(KebabifiedContext);

  const renderTooltip = () => {
    if (selectedItems.length === 0) {
      return i18n._(t`Select a row to approve`);
    }

    const itemsUnableToApprove = selectedItems
      .filter(cannotApprove)
      .map(item => item.name)
      .join(', ');

    if (selectedItems.some(cannotApprove)) {
      return i18n._(
        t`You are unable to act on the following workflow approvals: ${itemsUnableToApprove}`
      );
    }

    return i18n._(t`Approve`);
  };

  const isDisabled =
    selectedItems.length === 0 || selectedItems.some(cannotApprove);

  return (
    <>
      {isKebabified ? (
        <DropdownItem
          key="approve"
          isDisabled={isDisabled}
          component="button"
          onClick={onApprove}
        >
          {i18n._(t`Approve`)}
        </DropdownItem>
      ) : (
        <Tooltip content={renderTooltip()} position="top">
          <div>
            <Button
              isDisabled={isDisabled}
              aria-label={i18n._(t`Approve`)}
              variant="primary"
              onClick={onApprove}
            >
              {i18n._(t`Approve`)}
            </Button>
          </div>
        </Tooltip>
      )}
    </>
  );
}

WorkflowApprovalListApproveButton.propTypes = {
  onApprove: PropTypes.func.isRequired,
  selectedItems: PropTypes.arrayOf(WorkflowApproval),
};

WorkflowApprovalListApproveButton.defaultProps = {
  selectedItems: [],
};

export default withI18n()(WorkflowApprovalListApproveButton);
