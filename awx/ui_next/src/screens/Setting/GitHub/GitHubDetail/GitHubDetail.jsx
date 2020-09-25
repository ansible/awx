import React, { useEffect, useCallback } from 'react';
import { Link, Redirect, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { CardBody, CardActionsRow } from '../../../../components/Card';
import ContentError from '../../../../components/ContentError';
import ContentLoading from '../../../../components/ContentLoading';
import { DetailList } from '../../../../components/DetailList';
import RoutedTabs from '../../../../components/RoutedTabs';
import { useConfig } from '../../../../contexts/Config';
import { useSettings } from '../../../../contexts/Settings';
import useRequest from '../../../../util/useRequest';
import { SettingsAPI } from '../../../../api';
import SettingDetail from '../../shared';

function GitHubDetail({ i18n }) {
  const { me } = useConfig();
  const { GET: options } = useSettings();

  const baseURL = '/settings/github';
  const {
    path,
    params: { category },
  } = useRouteMatch(`${baseURL}/:category/details`);

  const { isLoading, error, request, result: gitHubDetails } = useRequest(
    useCallback(async () => {
      const [
        { data: gitHubDefault },
        { data: gitHubOrganization },
        { data: gitHubTeam },
      ] = await Promise.all([
        SettingsAPI.readCategory('github'),
        SettingsAPI.readCategory('github-org'),
        SettingsAPI.readCategory('github-team'),
      ]);
      return {
        default: gitHubDefault,
        organization: gitHubOrganization,
        team: gitHubTeam,
      };
    }, []),
    {
      default: null,
      organization: null,
      team: null,
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
          {i18n._(t`Back to Settings`)}
        </>
      ),
      link: `/settings`,
      id: 99,
    },
    {
      name: i18n._(t`GitHub Default`),
      link: `${baseURL}/default/details`,
      id: 0,
    },
    {
      name: i18n._(t`GitHub Organization`),
      link: `${baseURL}/organization/details`,
      id: 1,
    },
    {
      name: i18n._(t`GitHub Team`),
      link: `${baseURL}/team/details`,
      id: 2,
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
            {Object.keys(gitHubDetails[category]).map(key => {
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
              aria-label={i18n._(t`Edit`)}
              component={Link}
              to={`${baseURL}/${category}/edit`}
            >
              {i18n._(t`Edit`)}
            </Button>
          </CardActionsRow>
        )}
      </CardBody>
    </>
  );
}

export default withI18n()(GitHubDetail);
