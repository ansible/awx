import React, { Fragment } from 'react';
import {
  PageSection,
  PageSectionVariants,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbHeading
} from '@patternfly/react-core';
import {
  Link,
  Route,
  withRouter
} from 'react-router-dom';
import './breadcrumbs.scss';

const Breadcrumbs = ({ breadcrumbConfig }) => {
  const { light } = PageSectionVariants;

  return (
    <PageSection
      variant={light}
      className="pf-m-condensed"
    >
      <Breadcrumb>
        <Route
          render={(props) => <Crumb breadcrumbConfig={breadcrumbConfig} {...props} />}
        />
      </Breadcrumb>
    </PageSection>
  );
};

const Crumb = ({ breadcrumbConfig, match }) => {
  const crumb = breadcrumbConfig[match.url];

  let crumbElement = (
    <BreadcrumbItem key={match.url}>
      <Link to={match.url}>
        {crumb}
      </Link>
    </BreadcrumbItem>
  );

  if (match.isExact) {
    crumbElement = (
      <BreadcrumbHeading
        key="breadcrumb-heading"
        className="heading"
      >
        {crumb}
      </BreadcrumbHeading>
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
        render={(props) => <Crumb breadcrumbConfig={breadcrumbConfig} {...props} />}
      />
    </Fragment>
  );
};

export default withRouter(Breadcrumbs);
