import React, { Fragment } from 'react';
import { Trans } from '@lingui/macro';
import {
  PageSection,
  PageSectionVariants,
  Title,
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
              elem = (<Fragment key={name}>{name}</Fragment>);
            } else {
              elem = (
                <Link
                  key={name}
                  to={{ pathname: url, state: { breadcrumb: parentObj, organization } }}
                >
                  {name}
                </Link>
              );
            }
            return elem;
          })
          .reduce((prev, curr) => [prev, ' > ', curr])}
      </Fragment>
    );

    if (currentTab && currentTab !== 'details') {
      breadcrumb = (
        <Fragment>
          {generateCrumb()}
          {' > '}
          {getTabName(currentTab)}
        </Fragment>
      );
    } else if (location.pathname.indexOf('edit') > -1) {
      breadcrumb = (
        <Fragment>
          {generateCrumb()}
          <Trans>{' > edit'}</Trans>
        </Fragment>
      );
    } else if (location.pathname.indexOf('add') > -1) {
      breadcrumb = (
        <Fragment>
          {generateCrumb()}
          <Trans>{' > add'}</Trans>
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
      <Title size="2xl">{breadcrumb}</Title>
    </PageSection>
  );
};

export default OrganizationBreadcrumb;
