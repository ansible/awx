import React, { useEffect, useCallback } from 'react';
import { Link, Redirect, useRouteMatch } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { CardBody, CardActionsRow } from 'components/Card';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { DetailList } from 'components/DetailList';
import RoutedTabs from 'components/RoutedTabs';
import { useConfig } from 'contexts/Config';
import { useSettings } from 'contexts/Settings';
import useRequest from 'hooks/useRequest';
import { SettingsAPI } from 'api';
import { SettingDetail } from '../../shared';

function GitHubDetail() {
  const { me } = useConfig();
  const { GET: options } = useSettings();

  const baseURL = '/settings/github';
  const {
    path,
    params: { category },
  } = useRouteMatch(`${baseURL}/:category/details`);

  const {
    isLoading,
    error,
    request,
    result: gitHubDetails,
  } = useRequest(
    useCallback(async () => {
      const [
        { data: gitHubDefault },
        { data: gitHubOrganization },
        { data: gitHubTeam },
        { data: gitHubEnterprise },
        { data: gitHubEnterpriseOrganization },
        { data: gitHubEnterpriseTeam },
      ] = await Promise.all([
        SettingsAPI.readCategory('github'),
        SettingsAPI.readCategory('github-org'),
        SettingsAPI.readCategory('github-team'),
        SettingsAPI.readCategory('github-enterprise'),
        SettingsAPI.readCategory('github-enterprise-org'),
        SettingsAPI.readCategory('github-enterprise-team'),
      ]);
      return {
        default: gitHubDefault,
        organization: gitHubOrganization,
        team: gitHubTeam,
        enterprise: gitHubEnterprise,
        enterprise_organization: gitHubEnterpriseOrganization,
        enterprise_team: gitHubEnterpriseTeam,
      };
    }, []),
    {
      default: null,
      organization: null,
      team: null,
      enterprise: null,
      enterprise_organization: null,
      enterprise_team: null,
    }
  );

  useEffect(() => {
    request();
  }, [request]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Settings`}
        </>
      ),
      link: `/settings`,
      id: 99,
    },
    {
      name: t`GitHub Default`,
      link: `${baseURL}/default/details`,
      id: 0,
    },
    {
      name: t`GitHub Organization`,
      link: `${baseURL}/organization/details`,
      id: 1,
    },
    {
      name: t`GitHub Team`,
      link: `${baseURL}/team/details`,
      id: 2,
    },
    {
      name: t`GitHub Enterprise`,
      link: `${baseURL}/enterprise/details`,
      id: 3,
    },
    {
      name: t`GitHub Enterprise Organization`,
      link: `${baseURL}/enterprise_organization/details`,
      id: 4,
    },
    {
      name: t`GitHub Enterprise Team`,
      link: `${baseURL}/enterprise_team/details`,
      id: 5,
    },
  ];

  if (!Object.keys(gitHubDetails).includes(category)) {
    return <Redirect from={path} to={`${baseURL}/default/details`} exact />;
  }

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        {isLoading && <ContentLoading />}
        {!isLoading && error && <ContentError error={error} />}
        {!isLoading && !Object.values(gitHubDetails)?.includes(null) && (
          <DetailList>
            {Object.keys(gitHubDetails[category]).map((key) => {
              const record = options?.[key];
              return (
                <SettingDetail
                  key={key}
                  id={key}
                  helpText={record?.help_text}
                  label={record?.label}
                  type={record?.type}
                  unit={record?.unit}
                  value={gitHubDetails[category][key]}
                />
              );
            })}
          </DetailList>
        )}
        {me?.is_superuser && (
          <CardActionsRow>
            <Button
              ouiaId="github-detail-edit-button"
              aria-label={t`Edit`}
              component={Link}
              to={`${baseURL}/${category}/edit`}
            >
              {t`Edit`}
            </Button>
          </CardActionsRow>
        )}
      </CardBody>
    </>
  );
}

export default GitHubDetail;
