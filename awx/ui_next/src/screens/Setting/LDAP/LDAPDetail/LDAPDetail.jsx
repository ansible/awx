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
import { SettingsAPI } from '../../../../api';
import useRequest from '../../../../util/useRequest';
import { useConfig } from '../../../../contexts/Config';
import { useSettings } from '../../../../contexts/Settings';
import SettingDetail from '../../shared';
import { sortNestedDetails } from '../../shared/settingUtils';

function filterByPrefix(data, prefix) {
  return Object.keys(data)
    .filter(key => key.includes(prefix))
    .reduce((obj, key) => {
      obj[key] = data[key];
      return obj;
    }, {});
}

function LDAPDetail({ i18n }) {
  const { me } = useConfig();
  const { GET: options } = useSettings();
  const {
    path,
    params: { category },
  } = useRouteMatch('/settings/ldap/:category/details');

  const { isLoading, error, request, result: LDAPDetails } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('ldap');

      const mergedData = {};
      Object.keys(data).forEach(key => {
        if (key.includes('_CONNECTION_OPTIONS')) {
          return;
        }
        mergedData[key] = options[key];
        mergedData[key].value = data[key];
      });

      const ldap1 = filterByPrefix(mergedData, 'AUTH_LDAP_1_');
      const ldap2 = filterByPrefix(mergedData, 'AUTH_LDAP_2_');
      const ldap3 = filterByPrefix(mergedData, 'AUTH_LDAP_3_');
      const ldap4 = filterByPrefix(mergedData, 'AUTH_LDAP_4_');
      const ldap5 = filterByPrefix(mergedData, 'AUTH_LDAP_5_');
      const ldapDefault = Object.assign({}, mergedData);
      Object.keys({ ...ldap1, ...ldap2, ...ldap3, ...ldap4, ...ldap5 }).forEach(
        keyToOmit => {
          delete ldapDefault[keyToOmit];
        }
      );

      return {
        default: sortNestedDetails(ldapDefault),
        1: sortNestedDetails(ldap1),
        2: sortNestedDetails(ldap2),
        3: sortNestedDetails(ldap3),
        4: sortNestedDetails(ldap4),
        5: sortNestedDetails(ldap5),
      };
    }, [options]),
    {
      default: null,
      1: null,
      2: null,
      3: null,
      4: null,
      5: null,
    }
  );

  useEffect(() => {
    request();
  }, [request]);

  const baseURL = '/settings/ldap';
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
      name: i18n._(t`Default`),
      link: `${baseURL}/default/details`,
      id: 0,
    },
    {
      name: i18n._(t`LDAP1`),
      link: `${baseURL}/1/details`,
      id: 1,
    },
    {
      name: i18n._(t`LDAP2`),
      link: `${baseURL}/2/details`,
      id: 2,
    },
    {
      name: i18n._(t`LDAP3`),
      link: `${baseURL}/3/details`,
      id: 3,
    },
    {
      name: i18n._(t`LDAP4`),
      link: `${baseURL}/4/details`,
      id: 4,
    },
    {
      name: i18n._(t`LDAP5`),
      link: `${baseURL}/5/details`,
      id: 5,
    },
  ];

  if (!Object.keys(LDAPDetails).includes(category)) {
    return <Redirect from={path} to={`${baseURL}/default/details`} exact />;
  }

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        <>
          {isLoading && <ContentLoading />}
          {!isLoading && error && <ContentError error={error} />}
          {!isLoading && !Object.values(LDAPDetails)?.includes(null) && (
            <DetailList>
              {LDAPDetails[category].map(([key, detail]) => {
                return (
                  <SettingDetail
                    key={key}
                    id={key}
                    helpText={detail?.help_text}
                    label={detail?.label}
                    type={detail?.type}
                    unit={detail?.unit}
                    value={detail?.value}
                  />
                );
              })}
            </DetailList>
          )}
        </>
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

export default withI18n()(LDAPDetail);
