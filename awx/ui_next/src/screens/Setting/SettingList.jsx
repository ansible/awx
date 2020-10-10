import React from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Card as _Card,
  CardHeader as _CardHeader,
  CardTitle,
  DataList,
  DataListItem,
  DataListCell,
  DataListItemCells,
  DataListItemRow,
  PageSection,
} from '@patternfly/react-core';
import styled from 'styled-components';
import { BrandName } from '../../variables';
import { useConfig } from '../../contexts/Config';
import ContentLoading from '../../components/ContentLoading/ContentLoading';

// Setting BrandName to a variable here is necessary to get the jest tests
// passing.  Attempting to use BrandName in the template literal results
// in failing tests.
const brandName = BrandName;

const SplitLayout = styled(PageSection)`
  column-count: 1;
  column-gap: 24px;
  @media (min-width: 576px) {
    column-count: 2;
  }
`;
const Card = styled(_Card)`
  display: inline-block;
  margin-bottom: 24px;
  width: 100%;
`;
const CardHeader = styled(_CardHeader)`
  align-items: flex-start;
  display: flex;
  flex-flow: column nowrap;
  && > * {
    padding: 0;
  }
`;
const CardDescription = styled.div`
  color: var(--pf-global--palette--black-600);
  font-size: var(--pf-global--FontSize--xs);
`;

function SettingList({ i18n }) {
  const config = useConfig();
  const settingRoutes = [
    {
      header: i18n._(t`Authentication`),
      description: i18n._(
        t`Enable simplified login for your ${brandName} applications`
      ),
      id: 'authentication',
      routes: [
        {
          title: i18n._(t`Azure AD settings`),
          path: '/settings/azure',
        },
        {
          title: i18n._(t`GitHub settings`),
          path: '/settings/github',
        },
        {
          title: i18n._(t`Google OAuth 2 settings`),
          path: '/settings/google_oauth2',
        },
        {
          title: i18n._(t`LDAP settings`),
          path: '/settings/ldap',
        },
        {
          title: i18n._(t`RADIUS settings`),
          path: '/settings/radius',
        },
        {
          title: i18n._(t`SAML settings`),
          path: '/settings/saml',
        },
        {
          title: i18n._(t`TACACS+ settings`),
          path: '/settings/tacacs',
        },
      ],
    },
    {
      header: i18n._(t`Jobs`),
      description: i18n._(
        t`Update settings pertaining to Jobs within ${brandName}`
      ),
      id: 'jobs',
      routes: [
        {
          title: i18n._(t`Jobs settings`),
          path: '/settings/jobs',
        },
      ],
    },
    {
      header: i18n._(t`System`),
      description: i18n._(t`Define system-level features and functions`),
      id: 'system',
      routes: [
        {
          title: i18n._(t`Miscellaneous System settings`),
          path: '/settings/miscellaneous_system',
        },
        {
          title: i18n._(t`Activity Stream settings`),
          path: '/settings/activity_stream',
        },
        {
          title: i18n._(t`Logging settings`),
          path: '/settings/logging',
        },
      ],
    },
    {
      header: i18n._(t`User Interface`),
      description: i18n._(
        t`Set preferences for data collection, logos, and logins`
      ),
      id: 'ui',
      routes: [
        {
          title: i18n._(t`User Interface settings`),
          path: '/settings/ui',
        },
      ],
    },
    {
      header: i18n._(t`License`),
      description: i18n._(t`View and edit your license information`),
      id: 'license',
      routes: [
        {
          title: i18n._(t`License settings`),
          path: '/settings/license',
        },
      ],
    },
  ];

  if (Object.keys(config).length === 0) {
    return (
      <PageSection>
        <Card>
          <ContentLoading />
        </Card>
      </PageSection>
    );
  }

  return (
    <SplitLayout>
      {settingRoutes.map(({ description, header, id, routes }) => {
        if (id === 'license' && config?.license_info?.license_type === 'open') {
          return null;
        }
        return (
          <Card isCompact key={header}>
            <CardHeader>
              <CardTitle>{header}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
            <DataList aria-label={`${id}-settings`} isCompact>
              {routes.map(({ title, path }) => (
                <DataListItem key={title}>
                  <DataListItemRow>
                    <DataListItemCells
                      dataListCells={[
                        <DataListCell key={title}>
                          <Link to={path}>{title}</Link>
                        </DataListCell>,
                      ]}
                    />
                  </DataListItemRow>
                </DataListItem>
              ))}
            </DataList>
          </Card>
        );
      })}
    </SplitLayout>
  );
}

export default withI18n()(SettingList);
