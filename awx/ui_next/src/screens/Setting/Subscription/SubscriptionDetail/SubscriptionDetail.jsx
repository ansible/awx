import React from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import { Button, Label } from '@patternfly/react-core';
import {
  CaretLeftIcon,
  CheckIcon,
  ExclamationCircleIcon,
} from '@patternfly/react-icons';
import RoutedTabs from '../../../../components/RoutedTabs';
import { CardBody, CardActionsRow } from '../../../../components/Card';
import { DetailList, Detail } from '../../../../components/DetailList';
import { useConfig } from '../../../../contexts/Config';
import {
  formatDateString,
  formatDateStringUTC,
  secondsToDays,
} from '../../../../util/dates';

function SubscriptionDetail({ i18n }) {
  const { license_info, version } = useConfig();
  const baseURL = '/settings/subscription';
  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Settings`)}
        </>
      ),
      link: '/settings',
      id: 99,
    },
    {
      name: i18n._(t`Subscription Details`),
      link: `${baseURL}/details`,
      id: 0,
    },
  ];

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        <DetailList>
          <Detail
            dataCy="subscription-status"
            label={i18n._(t`Status`)}
            value={
              license_info.compliant ? (
                <Label variant="outline" color="green" icon={<CheckIcon />}>
                  {i18n._(t`Compliant`)}
                </Label>
              ) : (
                <Label
                  variant="outline"
                  color="red"
                  icon={<ExclamationCircleIcon />}
                >
                  {i18n._(t`Out of compliance`)}
                </Label>
              )
            }
          />
          <Detail
            dataCy="subscription-version"
            label={i18n._(t`Version`)}
            value={version}
          />
          <Detail
            dataCy="subscription-type"
            label={i18n._(t`Subscription type`)}
            value={license_info.license_type}
          />
          <Detail
            dataCy="subscription-name"
            label={i18n._(t`Subscription`)}
            value={license_info.subscription_name}
          />
          <Detail
            dataCy="subscription-trial"
            label={i18n._(t`Trial`)}
            value={license_info.trial ? i18n._(t`True`) : i18n._(t`False`)}
          />
          <Detail
            dataCy="subscription-expires-on-date"
            label={i18n._(t`Expires on`)}
            value={
              license_info.license_date &&
              formatDateString(
                new Date(license_info.license_date * 1000).toISOString()
              )
            }
          />
          <Detail
            dataCy="subscription-expires-on-utc-date"
            label={i18n._(t`Expires on UTC`)}
            value={
              license_info.license_date &&
              formatDateStringUTC(
                new Date(license_info.license_date * 1000).toISOString()
              )
            }
          />
          <Detail
            dataCy="subscription-days-remaining"
            label={i18n._(t`Days remaining`)}
            value={
              license_info.time_remaining &&
              secondsToDays(license_info.time_remaining)
            }
          />
          {license_info.instance_count < 9999999 && (
            <Detail
              dataCy="subscription-hosts-available"
              label={i18n._(t`Hosts available`)}
              value={license_info.available_instances}
            />
          )}
          {license_info.instance_count >= 9999999 && (
            <Detail
              dataCy="subscription-unlimited-hosts-available"
              label={i18n._(t`Hosts available`)}
              value={i18n._(t`Unlimited`)}
            />
          )}
          <Detail
            dataCy="subscription-hosts-used"
            label={i18n._(t`Hosts used`)}
            value={license_info.current_instances}
          />
          <Detail
            dataCy="subscription-hosts-remaining"
            label={i18n._(t`Hosts remaining`)}
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
        <CardActionsRow>
          <Button
            aria-label={i18n._(t`edit`)}
            component={Link}
            to="/settings/subscription/edit"
          >
            <Trans>Edit</Trans>
          </Button>
        </CardActionsRow>
      </CardBody>
    </>
  );
}

export default withI18n()(SubscriptionDetail);
