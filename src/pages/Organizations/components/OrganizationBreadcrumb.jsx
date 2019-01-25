import React, { Fragment } from 'react';
import { Trans } from '@lingui/macro';
import {
  PageSection,
  PageSectionVariants,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbHeading
} from '@patternfly/react-core';
import {
  Link
} from 'react-router-dom';

import getTabName from '../utils';

const OrganizationBreadcrumb = ({ parentObj, organization, currentTab, location }) => {
  const { light } = PageSectionVariants;
  let breadcrumb = '';
  if (parentObj !== 'loading') {
    const generateCrumb = (noLastLink = false) => (
      <Fragment>
        {parentObj
          .map(({ url, name }, index) => {
            let elem;
            if (noLastLink && parentObj.length - 1 === index) {
              elem = (<BreadcrumbHeading className="heading" key={name}>{name}</BreadcrumbHeading>);
            } else {
              elem = (
                <BreadcrumbItem key={name}>
                  <Link
                    key={name}
                    to={{ pathname: url, state: { breadcrumb: parentObj, organization } }}
                  >
                    {name}
                  </Link>
                </BreadcrumbItem>
              );
            }
            return elem;
          })
          .reduce((prev, curr) => [prev, curr])}
      </Fragment>
    );

    if (currentTab && currentTab !== 'details') {
      breadcrumb = (
        <Fragment>
          {generateCrumb()}
          <BreadcrumbHeading className="heading">
            {getTabName(currentTab)}
          </BreadcrumbHeading>
        </Fragment>
      );
    } else if (location.pathname.indexOf('edit') > -1) {
      breadcrumb = (
        <Fragment>
          {generateCrumb()}
          <BreadcrumbHeading className="heading">
            <Trans>Edit</Trans>
          </BreadcrumbHeading>
        </Fragment>
      );
    } else if (location.pathname.indexOf('add') > -1) {
      breadcrumb = (
        <Fragment>
          {generateCrumb()}
          <BreadcrumbHeading className="heading">
            <Trans>Add</Trans>
          </BreadcrumbHeading>
        </Fragment>
      );
    } else {
      breadcrumb = (
        <Fragment>
          {generateCrumb(true)}
        </Fragment>
      );
    }
  }

  return (
    <PageSection variant={light} className="pf-m-condensed">
      <Breadcrumb>{breadcrumb}</Breadcrumb>
    </PageSection>
  );
};

export default OrganizationBreadcrumb;
