import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import {
  PageSection as PFPageSection,
  PageSectionVariants,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbHeading,
} from '@patternfly/react-core';
import { Link, Route, withRouter, useRouteMatch } from 'react-router-dom';

import styled from 'styled-components';

const PageSection = styled(PFPageSection)`
  padding-top: 10px;
  padding-bottom: 10px;
`;

const Breadcrumbs = ({ breadcrumbConfig, match }) => {
  const { light } = PageSectionVariants;

  return (
    <PageSection variant={light}>
      <Breadcrumb>
        <Route path="/:path">
          <Crumb breadcrumbConfig={breadcrumbConfig} match={match} />
        </Route>
      </Breadcrumb>
    </PageSection>
  );
};

const Crumb = ({ breadcrumbConfig, match }) => {
  const crumb = breadcrumbConfig[match.url];

  let crumbElement = (
    <BreadcrumbItem key={match.url}>
      <Link to={match.url}>{crumb}</Link>
    </BreadcrumbItem>
  );

  if (match.isExact) {
    crumbElement = (
      <BreadcrumbHeading key="breadcrumb-heading">{crumb}</BreadcrumbHeading>
    );
  }

  if (!crumb) {
    crumbElement = null;
  }

  function NextCrumb() {
    const routeMatch = useRouteMatch();
    return <Crumb breadcrumbConfig={breadcrumbConfig} match={routeMatch} />;
  }

  return (
    <Fragment>
      {crumbElement}
      <Route path={`${match.url}/:path`}>
        <NextCrumb />
      </Route>
    </Fragment>
  );
};

Breadcrumbs.propTypes = {
  breadcrumbConfig: PropTypes.objectOf(PropTypes.string).isRequired,
};

Crumb.propTypes = {
  breadcrumbConfig: PropTypes.objectOf(PropTypes.string).isRequired,
};

export default withRouter(Breadcrumbs);
