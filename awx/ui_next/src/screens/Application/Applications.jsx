import React, { useState, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Route, Switch } from 'react-router-dom';
import {
  Alert,
  ClipboardCopy,
  ClipboardCopyVariant,
  Modal,
} from '@patternfly/react-core';
import ApplicationsList from './ApplicationsList';
import ApplicationAdd from './ApplicationAdd';
import Application from './Application';
import ScreenHeader from '../../components/ScreenHeader';
import { Detail, DetailList } from '../../components/DetailList';

const ApplicationAlert = styled(Alert)`
  margin-bottom: 20px;
`;

function Applications({ i18n }) {
  const [applicationModalSource, setApplicationModalSource] = useState(null);
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/applications': i18n._(t`Applications`),
    '/applications/add': i18n._(t`Create New Application`),
  });

  const buildBreadcrumbConfig = useCallback(
    application => {
      if (!application) {
        return;
      }
      setBreadcrumbConfig({
        '/applications': i18n._(t`Applications`),
        '/applications/add': i18n._(t`Create New Application`),
        [`/applications/${application.id}`]: `${application.name}`,
        [`/applications/${application.id}/edit`]: i18n._(t`Edit Details`),
        [`/applications/${application.id}/details`]: i18n._(t`Details`),
        [`/applications/${application.id}/tokens`]: i18n._(t`Tokens`),
      });
    },
    [i18n]
  );

  return (
    <>
      <ScreenHeader
        streamType="o_auth2_application,o_auth2_access_token"
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path="/applications/add">
          <ApplicationAdd
            onSuccessfulAdd={app => setApplicationModalSource(app)}
          />
        </Route>
        <Route path="/applications/:id">
          <Application setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/applications">
          <ApplicationsList />
        </Route>
      </Switch>
      {applicationModalSource && (
        <Modal
          aria-label={i18n._(t`Application information`)}
          isOpen
          variant="medium"
          title={i18n._(t`Application information`)}
          onClose={() => setApplicationModalSource(null)}
        >
          {applicationModalSource.client_secret && (
            <ApplicationAlert
              variant="info"
              isInline
              title={i18n._(
                t`This is the only time the client secret will be shown.`
              )}
            />
          )}
          <DetailList stacked>
            <Detail
              label={i18n._(t`Name`)}
              value={applicationModalSource.name}
            />
            {applicationModalSource.client_id && (
              <Detail
                label={i18n._(t`Client ID`)}
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
                label={i18n._(t`Client secret`)}
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

export default withI18n()(Applications);
