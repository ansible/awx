import React, { useCallback } from 'react';
import { number } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import useRequest, { useDismissableError } from '../../../util/useRequest';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import { ProjectsAPI } from '../../../api';

function ProjectSyncButton({ i18n, children, projectId }) {
  const { request: handleSync, error: syncError } = useRequest(
    useCallback(async () => {
      const { data } = await ProjectsAPI.readSync(projectId);
      if (data.can_update) {
        await ProjectsAPI.sync(projectId);
      } else {
        throw new Error(
          i18n._(
            t`You don't have the necessary permissions to sync this project.`
          )
        );
      }
    }, [i18n, projectId]),
    null
  );

  const { error, dismissError } = useDismissableError(syncError);

  return (
    <>
      {children(handleSync)}
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {i18n._(t`Failed to sync project.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

ProjectSyncButton.propTypes = {
  projectId: number.isRequired,
};

export default withI18n()(ProjectSyncButton);
