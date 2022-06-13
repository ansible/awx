import React from 'react';
import PropTypes from 'prop-types';
import useTitle from 'hooks/useTitle';

import { t } from '@lingui/macro';
import {
  Button,
  PageSection,
  PageSectionVariants,
  Breadcrumb,
  BreadcrumbItem,
  Title,
  Tooltip,
} from '@patternfly/react-core';
import { HistoryIcon } from '@patternfly/react-icons';
import { Link, Route, useRouteMatch, useLocation } from 'react-router-dom';

const ScreenHeader = ({ breadcrumbConfig, streamType }) => {
  const { light } = PageSectionVariants;
  const oneCrumbMatch = useRouteMatch({
    path: Object.keys(breadcrumbConfig)[0],
    strict: true,
  });

  const location = useLocation();
  const parts = location.pathname.split('/');
  if (parts.length > 2) {
    parts.pop();
  }

  const pathTitle = breadcrumbConfig[parts.join('/')];
  useTitle(pathTitle);

  const isOnlyOneCrumb = oneCrumbMatch && oneCrumbMatch.isExact;

  return (
    <PageSection variant={light}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          {!isOnlyOneCrumb && (
            <Breadcrumb ouiaId="breadcrumb-list">
              <Route path="/:path">
                <Crumb breadcrumbConfig={breadcrumbConfig} />
              </Route>
            </Breadcrumb>
          )}
          <div
            style={{
              minHeight: '31px',
            }}
          >
            <Route path="/:path">
              <ActualTitle breadcrumbConfig={breadcrumbConfig} />
            </Route>
          </div>
        </div>
        {streamType !== 'none' && (
          <div>
            <Tooltip content={t`View activity stream`} position="top">
              <Button
                ouiaId="activity-stream-button"
                aria-label={t`View activity stream`}
                variant="plain"
                component={Link}
                to={`/activity_stream${
                  streamType ? `?type=${streamType}` : ''
                }`}
              >
                <HistoryIcon />
              </Button>
            </Tooltip>
          </div>
        )}
      </div>
    </PageSection>
  );
};

const ActualTitle = ({ breadcrumbConfig }) => {
  const match = useRouteMatch();
  const title = breadcrumbConfig[match.url];
  let titleElement;

  if (match.isExact) {
    titleElement = (
      <Title size="2xl" headingLevel="h2" data-cy="screen-title">
        {title}
      </Title>
    );
  }

  if (!title) {
    titleElement = null;
  }

  return (
    <>
      {titleElement}
      <Route path={`${match.url}/:path`}>
        <ActualTitle breadcrumbConfig={breadcrumbConfig} />
      </Route>
    </>
  );
};

const Crumb = ({ breadcrumbConfig, showDivider }) => {
  const match = useRouteMatch();
  const crumb = breadcrumbConfig[match.url];

  let crumbElement = (
    <BreadcrumbItem key={match.url} showDivider={showDivider} data-cy={crumb}>
      <Link to={match.url}>{crumb}</Link>
    </BreadcrumbItem>
  );

  if (match.isExact) {
    crumbElement = null;
  }

  if (!crumb) {
    crumbElement = null;
  }
  return (
    <>
      {crumbElement}
      <Route path={`${match.url}/:path`}>
        <Crumb
          breadcrumbConfig={breadcrumbConfig}
          showDivider
          data-cy={crumb}
        />
      </Route>
    </>
  );
};

ScreenHeader.propTypes = {
  breadcrumbConfig: PropTypes.objectOf(PropTypes.string).isRequired,
};

Crumb.propTypes = {
  breadcrumbConfig: PropTypes.objectOf(PropTypes.string).isRequired,
};

export default ScreenHeader;
