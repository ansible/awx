import React, { useContext } from 'react';
import { Button } from '@patternfly/react-core';

import { t } from '@lingui/macro';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import AlertModal from 'components/AlertModal';

function LinkDeleteModal() {
  const dispatch = useContext(WorkflowDispatchContext);
  const { linkToDelete } = useContext(WorkflowStateContext);
  return (
    <AlertModal
      variant="danger"
      title={t`Remove Link`}
      isOpen={linkToDelete}
      onClose={() => dispatch({ type: 'SET_LINK_TO_DELETE', value: null })}
      actions={[
        <Button
          ouiaId="link-remove-confirm-button"
          id="confirm-link-removal"
          aria-label={t`Confirm link removal`}
          key="remove"
          onClick={() => dispatch({ type: 'DELETE_LINK' })}
          variant="danger"
        >
          {t`Remove`}
        </Button>,
        <Button
          ouiaId="link-remove-cancel-button"
          id="cancel-link-removal"
          aria-label={t`Cancel link removal`}
          key="cancel"
          onClick={() => dispatch({ type: 'SET_LINK_TO_DELETE', value: null })}
          variant="link"
        >
          {t`Cancel`}
        </Button>,
      ]}
    >
      <p>{t`Are you sure you want to remove this link?`}</p>
      {!linkToDelete.isConvergenceLink && (
        <>
          <br />
          <p>
            {t`Removing this link will orphan the rest of the branch and cause it to be executed immediately on launch.`}
          </p>
        </>
      )}
    </AlertModal>
  );
}

export default LinkDeleteModal;
