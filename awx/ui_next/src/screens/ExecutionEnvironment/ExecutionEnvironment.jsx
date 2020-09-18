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
import { Card, PageSection } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';

import useRequest from '../../util/useRequest';
import { ExecutionEnvironmentsAPI } from '../../api';
import RoutedTabs from '../../components/RoutedTabs';
import ContentError from '../../components/ContentError';
import ContentLoading from '../../components/ContentLoading';

import ExecutionEnvironmentDetails from './ExecutionEnvironmentDetails';
import ExecutionEnvironmentEdit from './ExecutionEnvironmentEdit';

function ExecutionEnvironment({ i18n, setBreadcrumb }) {
  const { id } = useParams();
  const { pathname } = useLocation();

  const {
    isLoading,
    error: contentError,
    request: fetchExecutionEnvironments,
    result: executionEnvironment,
  } = useRequest(
    useCallback(async () => {
      const { data } = await ExecutionEnvironmentsAPI.readDetail(id);
      return data;
    }, [id]),
    null
  );

  useEffect(() => {
    fetchExecutionEnvironments();
  }, [fetchExecutionEnvironments, pathname]);

  useEffect(() => {
    if (executionEnvironment) {
      setBreadcrumb(executionEnvironment);
    }
  }, [executionEnvironment, setBreadcrumb]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to execution environments`)}
        </>
      ),
      link: '/execution_environments',
      id: 99,
    },
    {
      name: i18n._(t`Details`),
      link: `/execution_environments/${id}/details`,
      id: 0,
    },
  ];

  if (!isLoading && contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError.response?.status === 404 && (
              <span>
                {i18n._(t`Execution environment not found.`)}{' '}
                <Link to="/execution_environments">
                  {i18n._(t`View all execution environments`)}
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
        {!isLoading && executionEnvironment && (
          <Switch>
            <Redirect
              from="/execution_environments/:id"
              to="/execution_environments/:id/details"
              exact
            />
            {executionEnvironment && (
              <>
                <Route path="/execution_environments/:id/edit">
                  <ExecutionEnvironmentEdit
                    executionEnvironment={executionEnvironment}
                  />
                </Route>
                <Route path="/execution_environments/:id/details">
                  <ExecutionEnvironmentDetails />
                </Route>
              </>
            )}
          </Switch>
        )}
      </Card>
    </PageSection>
  );
}

export default withI18n()(ExecutionEnvironment);
