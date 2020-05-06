import React, { Fragment, useContext } from 'react';
import { Button } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import AlertModal from '../../../../../components/AlertModal';

function LinkDeleteModal({ i18n }) {
  const dispatch = useContext(WorkflowDispatchContext);
  const { linkToDelete } = useContext(WorkflowStateContext);
  return (
    <AlertModal
      variant="danger"
      title="Remove Link"
      isOpen={linkToDelete}
      onClose={() => dispatch({ type: 'SET_LINK_TO_DELETE', value: null })}
      actions={[
        <Button
          id="confirm-link-removal"
          aria-label={i18n._(t`Confirm link removal`)}
          key="remove"
          onClick={() => dispatch({ type: 'DELETE_LINK' })}
          variant="danger"
        >
          {i18n._(t`Remove`)}
        </Button>,
        <Button
          id="cancel-link-removal"
          aria-label={i18n._(t`Cancel link removal`)}
          key="cancel"
          onClick={() => dispatch({ type: 'SET_LINK_TO_DELETE', value: null })}
          variant="secondary"
        >
          {i18n._(t`Cancel`)}
        </Button>,
      ]}
    >
      <p>{i18n._(t`Are you sure you want to remove this link?`)}</p>
      {!linkToDelete.isConvergenceLink && (
        <Fragment>
          <br />
          <p>
            {i18n._(
              t`Removing this link will orphan the rest of the branch and cause it to be executed immediately on launch.`
            )}
          </p>
        </Fragment>
      )}
    </AlertModal>
  );
}

export default withI18n()(LinkDeleteModal);
