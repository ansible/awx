import React, { Fragment } from 'react';
import { Button } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
import AlertModal from '@components/AlertModal';

function LinkDeleteModal({ i18n, linkToDelete, onConfirm, onCancel }) {
  return (
    <AlertModal
      variant="danger"
      title="Remove Link"
      isOpen={linkToDelete}
      onClose={onCancel}
      actions={[
        <Button
          aria-label={i18n._(t`Confirm link removal`)}
          key="remove"
          onClick={() => onConfirm()}
          variant="danger"
        >
          {i18n._(t`Remove`)}
        </Button>,
        <Button
          aria-label={i18n._(t`Cancel link removal`)}
          key="cancel"
          onClick={onCancel}
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

LinkDeleteModal.propTypes = {
  linkToDelete: shape().isRequired,
  onCancel: func.isRequired,
  onConfirm: func.isRequired,
};

export default withI18n()(LinkDeleteModal);
