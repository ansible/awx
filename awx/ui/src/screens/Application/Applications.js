import React, { useState, useCallback } from 'react';

import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Route, Switch } from 'react-router-dom';
import {
  Alert,
  ClipboardCopy,
  ClipboardCopyVariant,
  Modal,
} from '@patternfly/react-core';
import ScreenHeader from 'components/ScreenHeader';
import { Detail, DetailList } from 'components/DetailList';
import PersistentFilters from 'components/PersistentFilters';
import ApplicationsList from './ApplicationsList';
import ApplicationAdd from './ApplicationAdd';
import Application from './Application';

const ApplicationAlert = styled(Alert)`
  margin-bottom: 20px;
`;

function Applications() {
  const [applicationModalSource, setApplicationModalSource] = useState(null);
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/applications': t`Applications`,
    '/applications/add': t`Create New Application`,
  });

  const buildBreadcrumbConfig = useCallback((application) => {
    if (!application) {
      return;
    }
    setBreadcrumbConfig({
      '/applications': t`Applications`,
      '/applications/add': t`Create New Application`,
      [`/applications/${application.id}`]: `${application.name}`,
      [`/applications/${application.id}/edit`]: t`Edit Details`,
      [`/applications/${application.id}/details`]: t`Details`,
      [`/applications/${application.id}/tokens`]: t`Tokens`,
    });
  }, []);

  return (
    <>
      <ScreenHeader
        streamType="o_auth2_application,o_auth2_access_token"
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path="/applications/add">
          <ApplicationAdd
            onSuccessfulAdd={(app) => setApplicationModalSource(app)}
          />
        </Route>
        <Route path="/applications/:id">
          <Application setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/applications">
          <PersistentFilters pageKey="applications">
            <ApplicationsList />
          </PersistentFilters>
        </Route>
      </Switch>
      {applicationModalSource && (
        <Modal
          aria-label={t`Application information`}
          isOpen
          variant="medium"
          title={t`Application information`}
          onClose={() => setApplicationModalSource(null)}
        >
          {applicationModalSource.client_secret && (
            <ApplicationAlert
              variant="info"
              isInline
              title={t`This is the only time the client secret will be shown.`}
            />
          )}
          <DetailList stacked>
            <Detail label={t`Name`} value={applicationModalSource.name} />
            {applicationModalSource.client_id && (
              <Detail
                label={t`Client ID`}
                value={
                  <ClipboardCopy
                    isReadOnly
                    variant={ClipboardCopyVariant.expansion}
                  >
                    {applicationModalSource.client_id}
                  </ClipboardCopy>
                }
              />
            )}
            {applicationModalSource.client_secret && (
              <Detail
                label={t`Client secret`}
                value={
                  <ClipboardCopy
                    isReadOnly
                    variant={ClipboardCopyVariant.expansion}
                  >
                    {applicationModalSource.client_secret}
                  </ClipboardCopy>
                }
              />
            )}
          </DetailList>
        </Modal>
      )}
    </>
  );
}

export default Applications;
