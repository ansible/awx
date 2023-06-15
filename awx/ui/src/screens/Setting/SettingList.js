import React from 'react';
import { Link } from 'react-router-dom';
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
import { useConfig } from 'contexts/Config';
import ContentLoading from 'components/ContentLoading/ContentLoading';
import useBrandName from 'hooks/useBrandName';

const SplitLayout = styled(PageSection)`
  column-count: 1;
  column-gap: 24px;
  @media (min-width: 576px) {
    column-count: 2;
  }
`;
const Card = styled(_Card)`
  && {
    display: inline-block;
    margin-bottom: 24px;
    width: 100%;
  }
`;
const CardHeader = styled(_CardHeader)`
  && {
    align-items: flex-start;
    display: flex;
    flex-flow: column nowrap;
  }
`;
const CardDescription = styled.div`
  color: var(--pf-global--palette--black-600);
  font-size: var(--pf-global--FontSize--xs);
`;

function SettingList() {
  const config = useConfig();
  const brandName = useBrandName();

  const settingRoutes = [
    {
      header: t`Authentication`,
      description: t`Enable simplified login for your ${brandName} applications`,
      id: 'authentication',
      routes: [
        {
          title: t`Azure AD settings`,
          path: '/settings/azure',
        },
        {
          title: t`GitHub settings`,
          path: '/settings/github',
        },
        {
          title: t`Google OAuth 2 settings`,
          path: '/settings/google_oauth2',
        },
        {
          title: t`LDAP settings`,
          path: '/settings/ldap',
        },
        {
          title: t`RADIUS settings`,
          path: '/settings/radius',
        },
        {
          title: t`SAML settings`,
          path: '/settings/saml',
        },
        {
          title: t`TACACS+ settings`,
          path: '/settings/tacacs',
        },
        {
          title: t`Generic OIDC settings`,
          path: '/settings/oidc',
        },
      ],
    },
    {
      header: t`Jobs`,
      description: t`Update settings pertaining to Jobs within ${brandName}`,
      id: 'jobs',
      routes: [
        {
          title: t`Jobs settings`,
          path: '/settings/jobs',
        },
      ],
    },
    {
      header: t`System`,
      description: t`Define system-level features and functions`,
      id: 'system',
      routes: [
        {
          title: t`Miscellaneous System settings`,
          path: '/settings/miscellaneous_system',
        },
        {
          title: t`Miscellaneous Authentication settings`,
          path: '/settings/miscellaneous_authentication',
        },
        {
          title: t`Logging settings`,
          path: '/settings/logging',
        },
      ],
    },
    {
      header: t`User Interface`,
      description: t`Set preferences for data collection, logos, and logins`,
      id: 'ui',
      routes: [
        {
          title: t`User Interface settings`,
          path: '/settings/ui',
        },
      ],
    },
    {
      header: t`Subscription`,
      description: t`View and edit your subscription information`,
      id: 'subscription',
      routes: [
        {
          title: t`Subscription settings`,
          path: '/settings/subscription',
        },
      ],
    },
    {
      header: t`Troubleshooting`,
      description: t`View and edit debug options`,
      id: 'troubleshooting',
      routes: [
        {
          title: t`Troubleshooting settings`,
          path: '/settings/troubleshooting',
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
        if (
          id === 'subscription' &&
          config?.license_info?.license_type === 'open'
        ) {
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

export default SettingList;
