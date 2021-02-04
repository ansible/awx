import React, { useCallback } from 'react';
import { useRouteMatch } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import { SyncIcon } from '@patternfly/react-icons';

import { number } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import useRequest, { useDismissableError } from '../../../util/useRequest';

import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import { ProjectsAPI } from '../../../api';

function ProjectSyncButton({ i18n, projectId }) {
  const match = useRouteMatch();

  const { request: handleSync, error: syncError } = useRequest(
    useCallback(async () => {
      await ProjectsAPI.sync(projectId);
    }, [projectId]),
    null
  );

  const { error, dismissError } = useDismissableError(syncError);
  const isDetailsView = match.url.endsWith('/details');
  return (
    <>
      <Button
        aria-label={i18n._(t`Sync Project`)}
        variant={isDetailsView ? 'secondary' : 'plain'}
        onClick={handleSync}
      >
        {match.url.endsWith('/details') ? i18n._(t`Sync`) : <SyncIcon />}
      </Button>
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
