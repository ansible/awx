import React, { useCallback, useEffect } from 'react';
import { t } from '@lingui/macro';

import { Switch, Route, Redirect, Link, useRouteMatch } from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import { useConfig } from 'contexts/Config';
import ContentError from 'components/ContentError';
import RoutedTabs from 'components/RoutedTabs';
import useRequest from 'hooks/useRequest';
import { SettingsAPI } from 'api';
import ContentLoading from 'components/ContentLoading';
import InstanceDetail from './InstanceDetail';
import InstancePeerList from './InstancePeers';
import InstanceEndPointList from './InstanceEndPointList';

function Instance({ setBreadcrumb }) {
  const { me } = useConfig();
  const canReadSettings = me.is_superuser || me.is_system_auditor;

  const match = useRouteMatch();
  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Instances`}
        </>
      ),
      link: `/instances`,
      id: 99,
      persistentFilterKey: 'instances',
    },
    { name: t`Details`, link: `${match.url}/details`, id: 0 },
  ];

  const {
    result: isK8s,
    error,
    isLoading,
    request,
  } = useRequest(
    useCallback(async () => {
      if (!canReadSettings) {
        return false;
      }
      const { data } = await SettingsAPI.readCategory('system');
      return data?.IS_K8S ?? false;
    }, [canReadSettings]),
    { isK8s: false, isLoading: true }
  );

  useEffect(() => {
    request();
  }, [request]);

  if (isK8s) {
    tabsArray.push({ name: t`Endpoints`, link: `${match.url}/endpoints`, id: 1 });
    tabsArray.push({ name: t`Peers`, link: `${match.url}/peers`, id: 2 });
  }
  if (isLoading) {
    return <ContentLoading />;
  }

  if (error) {
    return <ContentError />;
  }
  return (
    <PageSection>
      <Card>
        <RoutedTabs tabsArray={tabsArray} />
        <Switch>
          <Redirect from="/instances/:id" to="/instances/:id/details" exact />
          <Route path="/instances/:id/details" key="details">
            <InstanceDetail isK8s={isK8s} setBreadcrumb={setBreadcrumb} />
          </Route>
          {isK8s && (
            <Route path="/instances/:id/endpoints" key="endpoints">
              <InstanceEndPointList setBreadcrumb={setBreadcrumb} />
            </Route>
          )}
          {isK8s && (
            <Route path="/instances/:id/peers" key="peers">
              <InstancePeerList setBreadcrumb={setBreadcrumb} />
            </Route>
          )}
          <Route path="*" key="not-found">
            <ContentError isNotFound>
              {match.params.id && (
                <Link to={`/instances/${match.params.id}/details`}>
                  {t`View Instance Details`}
                </Link>
              )}
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default Instance;
