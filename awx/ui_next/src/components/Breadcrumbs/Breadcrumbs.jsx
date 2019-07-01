import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import {
  PageSection as PFPageSection,
  PageSectionVariants,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbHeading as PFBreadcrumbHeading,
} from '@patternfly/react-core';
import { Link, Route, withRouter } from 'react-router-dom';
import styled from 'styled-components';

const PageSection = styled(PFPageSection)`
  padding-top: 10px;
  padding-bottom: 10px;
`;

const BreadcrumbHeading = styled(PFBreadcrumbHeading)`
  --pf-c-breadcrumb__heading--FontSize: 20px;
  line-height: 24px;
  flex: 100%;
`;

const Breadcrumbs = ({ breadcrumbConfig }) => {
  const { light } = PageSectionVariants;

  return (
    <PageSection variant={light}>
      <Breadcrumb>
        <Route
          path="/:path"
          render={props => (
            <Crumb breadcrumbConfig={breadcrumbConfig} {...props} />
          )}
        />
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

  return (
    <Fragment>
      {crumbElement}
      <Route
        path={`${match.url}/:path`}
        render={props => (
          <Crumb breadcrumbConfig={breadcrumbConfig} {...props} />
        )}
      />
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
