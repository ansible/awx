import React, { useEffect, useCallback } from 'react';
import {
  Link,
  Redirect,
  Route,
  Switch,
  useLocation,
  useParams,
} from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';

import useRequest from '../../util/useRequest';
import { InstanceGroupsAPI } from '../../api';
import RoutedTabs from '../../components/RoutedTabs';
import ContentError from '../../components/ContentError';
import ContentLoading from '../../components/ContentLoading';
import JobList from '../../components/JobList';

import ContainerGroupDetails from './ContainerGroupDetails';
import ContainerGroupEdit from './ContainerGroupEdit';

function ContainerGroup({ i18n, setBreadcrumb }) {
  const { id } = useParams();
  const { pathname } = useLocation();

  const {
    isLoading,
    error: contentError,
    request: fetchInstanceGroups,
    result: instanceGroup,
  } = useRequest(
    useCallback(async () => {
      const { data } = await InstanceGroupsAPI.readDetail(id);
      return data;
    }, [id])
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
          {i18n._(t`Back to instance groups`)}
        </>
      ),
      link: '/instance_groups',
      id: 99,
    },
    {
      name: i18n._(t`Details`),
      link: `/instance_groups/container_group/${id}/details`,
      id: 0,
    },
    {
      name: i18n._(t`Jobs`),
      link: `/instance_groups/container_group/${id}/jobs`,
      id: 1,
    },
  ];

  if (!isLoading && contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError.response?.status === 404 && (
              <span>
                {i18n._(t`Container group not found.`)}
                {''}
                <Link to="/instance_groups">
                  {i18n._(t`View all instance groups`)}
                </Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  let cardHeader = <RoutedTabs tabsArray={tabsArray} />;
  if (pathname.endsWith('edit')) {
    cardHeader = null;
  }

  return (
    <PageSection>
      <Card>
        {cardHeader}
        {isLoading && <ContentLoading />}
        {!isLoading && instanceGroup && (
          <Switch>
            <Redirect
              from="/instance_groups/container_group/:id"
              to="/instance_groups/container_group/:id/details"
              exact
            />
            {instanceGroup && (
              <>
                <Route path="/instance_groups/container_group/:id/edit">
                  <ContainerGroupEdit instanceGroup={instanceGroup} />
                </Route>
                <Route path="/instance_groups/container_group/:id/details">
                  <ContainerGroupDetails instanceGroup={instanceGroup} />
                </Route>
                <Route path="/instance_groups/container_group/:id/jobs">
                  <JobList
                    showTypeColumn
                    defaultParams={{ instance_group: instanceGroup.id }}
                  />
                </Route>
              </>
            )}
          </Switch>
        )}
      </Card>
    </PageSection>
  );
}

export default withI18n()(ContainerGroup);
