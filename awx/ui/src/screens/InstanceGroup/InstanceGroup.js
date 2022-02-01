import React, { useEffect, useCallback } from 'react';
import {
  Link,
  Redirect,
  Route,
  Switch,
  useLocation,
  useParams,
  useRouteMatch,
} from 'react-router-dom';

import { t } from '@lingui/macro';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import { HeaderRow, HeaderCell } from 'components/PaginatedTable';
import { getQSConfig } from 'util/qs';
import useRequest from 'hooks/useRequest';
import { InstanceGroupsAPI, SettingsAPI } from 'api';
import RoutedTabs from 'components/RoutedTabs';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import JobList from 'components/JobList';

import { InstanceList } from 'components/Instances';
import InstanceDetail from 'components/InstanceDetail';
import InstanceGroupDetails from './InstanceGroupDetails';
import InstanceGroupEdit from './InstanceGroupEdit';

const QS_CONFIG = getQSConfig('instance', {
  page: 1,
  page_size: 20,
  order_by: 'hostname',
});
function InstanceGroup({ setBreadcrumb }) {
  const { id } = useParams();
  const { pathname } = useLocation();
  const match = useRouteMatch();

  const {
    isLoading,
    error: contentError,
    request: fetchInstanceGroups,
    result: { instanceGroup, defaultControlPlane, defaultExecution },
  } = useRequest(
    useCallback(async () => {
      const [
        { data },
        {
          data: {
            DEFAULT_CONTROL_PLANE_QUEUE_NAME,
            DEFAULT_EXECUTION_QUEUE_NAME,
          },
        },
      ] = await Promise.all([
        InstanceGroupsAPI.readDetail(id),
        SettingsAPI.readAll(),
      ]);

      return {
        instanceGroup: data,
        defaultControlPlane: DEFAULT_CONTROL_PLANE_QUEUE_NAME,
        defaultExecution: DEFAULT_EXECUTION_QUEUE_NAME,
      };
    }, [id]),
    { instanceGroup: null, defaultControlPlane: '', defaultExecution: '' }
  );

  useEffect(() => {
    fetchInstanceGroups();
  }, [fetchInstanceGroups, pathname]);

  useEffect(() => {
    if (instanceGroup) {
      setBreadcrumb(instanceGroup);
    }
  }, [instanceGroup, setBreadcrumb]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Instance Groups`}
        </>
      ),
      link: '/instance_groups',
      id: 99,
    },
    {
      name: t`Details`,
      link: `/instance_groups/${id}/details`,
      id: 0,
    },
    {
      name: t`Instances`,
      link: `/instance_groups/${id}/instances`,
      id: 1,
    },
    {
      name: t`Jobs`,
      link: `/instance_groups/${id}/jobs`,
      id: 2,
    },
  ];

  if (!isLoading && contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError.response?.status === 404 && (
              <span>
                {t`Instance group not found.`}
                {''}
                <Link to="/instance_groups">{t`View all instance groups`}</Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  let cardHeader = <RoutedTabs tabsArray={tabsArray} />;

  if (['edit', 'instances/'].some((name) => pathname.includes(name))) {
    cardHeader = null;
  }

  return (
    <PageSection>
      <Card>
        {cardHeader}
        {isLoading && <ContentLoading />}
        {!isLoading && instanceGroup && (
          <>
            <Switch>
              <Redirect
                from="/instance_groups/:id/instances/:instanceId"
                to="/instance_groups/:id/instances/:instanceId/details"
                exact
              />
              <Route
                key="details"
                path="/instance_groups/:id/instances/:instanceId/details"
              >
                <InstanceDetail
                  setBreadcrumb={setBreadcrumb}
                  instanceGroup={instanceGroup}
                />
              </Route>
              <Route key="instanceList" path="/instance_groups/:id/instances">
                <InstanceList
                  headerRow={
                    <HeaderRow qsConfig={QS_CONFIG} isExpandable>
                      <HeaderCell sortKey="hostname">{t`Name`}</HeaderCell>
                      <HeaderCell sortKey="errors">{t`Status`}</HeaderCell>
                      <HeaderCell>{t`Running Jobs`}</HeaderCell>
                      <HeaderCell>{t`Total Jobs`}</HeaderCell>
                      <HeaderCell>{t`Capacity Adjustment`}</HeaderCell>
                      <HeaderCell>{t`Used Capacity`}</HeaderCell>
                      <HeaderCell>{t`Actions`}</HeaderCell>
                    </HeaderRow>
                  }
                  QS_CONFIG={QS_CONFIG}
                />
              </Route>
              <Redirect
                from="/instance_groups/:id"
                to="/instance_groups/:id/details"
                exact
              />
              <Route path="/instance_groups/:id/edit">
                <InstanceGroupEdit
                  instanceGroup={instanceGroup}
                  defaultExecution={defaultExecution}
                  defaultControlPlane={defaultControlPlane}
                />
              </Route>
              <Route path="/instance_groups/:id/details">
                <InstanceGroupDetails
                  defaultExecution={defaultExecution}
                  defaultControlPlane={defaultControlPlane}
                  instanceGroup={instanceGroup}
                />
              </Route>
              <Route path="/instance_groups/:id/jobs">
                <JobList
                  showTypeColumn
                  defaultParams={{ instance_group: instanceGroup.id }}
                />
              </Route>
              ,
              <Route path="*" key="not-found">
                <ContentError isNotFound>
                  {match.params.id && (
                    <Link
                      to={`$/instance_groups/${instanceGroup.id}/details`}
                    >{t`View Instance Group Details`}</Link>
                  )}
                </ContentError>
              </Route>
            </Switch>
          </>
        )}
      </Card>
    </PageSection>
  );
}

export default InstanceGroup;
