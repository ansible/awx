import React from 'react';
import { Link } from 'react-router-dom';

import { t, Trans } from '@lingui/macro';
import { Button, Label } from '@patternfly/react-core';
import {
  CaretLeftIcon,
  CheckIcon,
  ExclamationCircleIcon,
} from '@patternfly/react-icons';
import RoutedTabs from 'components/RoutedTabs';
import { CardBody, CardActionsRow } from 'components/Card';
import { DetailList, Detail } from 'components/DetailList';
import { useConfig } from 'contexts/Config';
import { formatDateString, secondsToDays } from 'util/dates';

function SubscriptionDetail() {
  const { me = {}, license_info, version } = useConfig();
  const baseURL = '/settings/subscription';
  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Settings`}
        </>
      ),
      link: '/settings',
      id: 99,
    },
    {
      name: t`Subscription Details`,
      link: `${baseURL}/details`,
      id: 0,
    },
  ];

  const { automated_instances: automatedInstancesCount, automated_since } =
    license_info;

  const automatedInstancesSinceDateTime = automated_since
    ? formatDateString(new Date(automated_since * 1000).toISOString())
    : null;

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        <DetailList>
          <Detail
            dataCy="subscription-status"
            label={t`Status`}
            value={
              license_info.compliant ? (
                <Label variant="outline" color="green" icon={<CheckIcon />}>
                  {t`Compliant`}
                </Label>
              ) : (
                <Label
                  variant="outline"
                  color="red"
                  icon={<ExclamationCircleIcon />}
                >
                  {t`Out of compliance`}
                </Label>
              )
            }
          />
          <Detail
            dataCy="subscription-version"
            label={t`Version`}
            value={version}
          />
          <Detail
            dataCy="subscription-type"
            label={t`Subscription type`}
            value={license_info.license_type}
          />
          <Detail
            dataCy="subscription-name"
            label={t`Subscription`}
            value={license_info.subscription_name}
          />
          <Detail
            dataCy="subscription-trial"
            label={t`Trial`}
            value={license_info.trial ? t`True` : t`False`}
          />
          <Detail
            dataCy="subscription-expires-on-date"
            label={t`Expires on`}
            value={
              license_info.license_date &&
              formatDateString(
                new Date(license_info.license_date * 1000).toISOString()
              )
            }
          />
          <Detail
            dataCy="subscription-expires-on-utc-date"
            label={t`Expires on UTC`}
            value={
              license_info.license_date &&
              formatDateString(
                new Date(license_info.license_date * 1000).toISOString(),
                'UTC'
              )
            }
          />
          <Detail
            dataCy="subscription-days-remaining"
            label={t`Days remaining`}
            value={
              license_info.time_remaining &&
              secondsToDays(license_info.time_remaining)
            }
          />
          {license_info.instance_count < 9999999 && (
            <Detail
              dataCy="subscription-hosts-available"
              label={t`Hosts available`}
              value={license_info.available_instances}
            />
          )}
          {license_info.instance_count >= 9999999 && (
            <Detail
              dataCy="subscription-unlimited-hosts-available"
              label={t`Hosts available`}
              value={t`Unlimited`}
            />
          )}
          <Detail
            dataCy="subscription-hosts-imported"
            label={t`Hosts imported`}
            value={license_info.current_instances}
          />
          {typeof automatedInstancesCount !== 'undefined' &&
            automatedInstancesCount !== null && (
              <Detail
                dataCy="subscription-hosts-automated"
                label={t`Hosts automated`}
                value={
                  automated_since ? (
                    <Trans>
                      {automatedInstancesCount} since{' '}
                      {automatedInstancesSinceDateTime}
                    </Trans>
                  ) : (
                    automatedInstancesCount
                  )
                }
              />
            )}
          <Detail
            dataCy="subscription-hosts-remaining"
            label={t`Hosts remaining`}
            value={license_info.free_instances}
          />
        </DetailList>
        <br />
        <Trans>
          If you are ready to upgrade or renew, please{' '}
          <Button
            component="a"
            href="https://www.redhat.com/contact"
            variant="link"
            target="_blank"
            isInline
          >
            contact us.
          </Button>
        </Trans>
        {me.is_superuser && (
          <CardActionsRow>
            <Button
              aria-label={t`edit`}
              component={Link}
              to="/settings/subscription/edit"
            >
              <Trans>Edit</Trans>
            </Button>
          </CardActionsRow>
        )}
      </CardBody>
    </>
  );
}

export default SubscriptionDetail;
