import React, { useState } from 'react';

import { Trans, t } from '@lingui/macro';
import { useField, useFormikContext } from 'formik';
import styled from 'styled-components';
import { TimesIcon } from '@patternfly/react-icons';
import {
  Button,
  Divider,
  FileUpload,
  Flex,
  FlexItem,
  FormGroup,
  ToggleGroup,
  ToggleGroupItem,
  Tooltip,
} from '@patternfly/react-core';
import { useConfig } from 'contexts/Config';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import useModal from 'hooks/useModal';
import FormField, { PasswordField } from 'components/FormField';
import Popover from 'components/Popover';
import SubscriptionModal from './SubscriptionModal';

const LICENSELINK = 'https://www.ansible.com/license';
const FileUploadField = styled(FormGroup)`
  && {
    max-width: 500px;
    width: 100%;
  }
`;

function SubscriptionStep() {
  const config = useConfig();
  const hasValidKey = Boolean(config?.license_info?.valid_key);

  const { values } = useFormikContext();

  const [isSelected, setIsSelected] = useState(
    values.subscription ? 'selectSubscription' : 'uploadManifest'
  );
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const [manifest, manifestMeta, manifestHelpers] = useField('manifest_file');
  const [manifestFilename, , manifestFilenameHelpers] =
    useField('manifest_filename');
  const [subscription, , subscriptionHelpers] = useField('subscription');
  const [username, usernameMeta, usernameHelpers] = useField('username');
  const [password, passwordMeta, passwordHelpers] = useField('password');

  return (
    <Flex
      direction={{ default: 'column' }}
      spaceItems={{ default: 'spaceItemsMd' }}
      alignItems={{ default: 'alignItemsBaseline' }}
    >
      {!hasValidKey && (
        <>
          <b>
            {t`Welcome to Red Hat Ansible Automation Platform!
              Please complete the steps below to activate your subscription.`}
          </b>
          <p>
            {t`If you do not have a subscription, you can visit
            Red Hat to obtain a trial subscription.`}
          </p>
          <Button
            aria-label={t`Request subscription`}
            component="a"
            href={LICENSELINK}
            ouiaId="request-subscription-button"
            target="_blank"
            variant="secondary"
            rel="noopener noreferrer"
          >
            {t`Request subscription`}
          </Button>
          <Divider />
        </>
      )}
      <p>{t`Select your Ansible Automation Platform subscription to use.`}</p>
      <ToggleGroup>
        <ToggleGroupItem
          text={t`Subscription manifest`}
          isSelected={isSelected === 'uploadManifest'}
          onChange={() => setIsSelected('uploadManifest')}
          id="subscription-manifest"
        />
        <ToggleGroupItem
          text={t`Username / password`}
          isSelected={isSelected === 'selectSubscription'}
          onChange={() => setIsSelected('selectSubscription')}
          id="username-password"
        />
      </ToggleGroup>
      {isSelected === 'uploadManifest' ? (
        <>
          <p>
            <Trans>
              Upload a Red Hat Subscription Manifest containing your
              subscription. To generate your subscription manifest, go to{' '}
              <Button
                component="a"
                href="https://access.redhat.com/management/subscription_allocations"
                variant="link"
                target="_blank"
                ouiaId="subscription-allocations-link"
                rel="noopener noreferrer"
                isInline
              >
                subscription allocations
              </Button>{' '}
              on the Red Hat Customer Portal.
            </Trans>
          </p>
          <FileUploadField
            fieldId="subscription-manifest"
            validated={manifestMeta.error ? 'error' : 'default'}
            helperTextInvalid={t`Invalid file format. Please upload a valid Red Hat Subscription Manifest.`}
            label={t`Red Hat subscription manifest`}
            helperText={t`Upload a .zip file`}
            labelIcon={
              <Popover
                content={
                  <Trans>
                    A subscription manifest is an export of a Red Hat
                    Subscription. To generate a subscription manifest, go to{' '}
                    <Button
                      component="a"
                      href="https://access.redhat.com/management/subscription_allocations"
                      variant="link"
                      target="_blank"
                      rel="noopener noreferrer"
                      isInline
                      ouiaId="subscription-allocations-link"
                    >
                      access.redhat.com
                    </Button>
                    . For more information, see the{' '}
                    <Button
                      component="a"
                      href={`${getDocsBaseUrl(
                        config
                      )}/html/userguide/import_license.html`}
                      variant="link"
                      target="_blank"
                      rel="noopener noreferrer"
                      ouiaId="import-license-link"
                      isInline
                    >
                      User Guide
                    </Button>
                    .
                  </Trans>
                }
              />
            }
          >
            <FileUpload
              id="upload-manifest"
              value={manifest.value}
              filename={manifestFilename.value}
              browseButtonText={t`Browse`}
              isDisabled={!config?.me?.is_superuser}
              dropzoneProps={{
                accept: '.zip',
                onDropRejected: () => manifestHelpers.setError(true),
              }}
              onChange={(value, filename) => {
                if (!value) {
                  manifestHelpers.setValue(null);
                  manifestFilenameHelpers.setValue('');
                  usernameHelpers.setValue(usernameMeta.initialValue);
                  passwordHelpers.setValue(passwordMeta.initialValue);
                  return;
                }

                try {
                  const raw = new FileReader();
                  raw.readAsBinaryString(value);
                  raw.onload = () => {
                    const rawValue = btoa(raw.result);
                    manifestHelpers.setValue(rawValue);
                    manifestFilenameHelpers.setValue(filename);
                  };
                } catch (err) {
                  manifestHelpers.setError(err);
                }
              }}
            />
          </FileUploadField>
        </>
      ) : (
        <>
          <p>
            {t`Provide your Red Hat or Red Hat Satellite credentials
                 below and you can choose from a list of your available subscriptions.
                 The credentials you use will be stored for future use in
                 retrieving renewal or expanded subscriptions.`}
          </p>
          <Flex
            direction={{ default: 'column', md: 'row' }}
            spaceItems={{ default: 'spaceItemsMd' }}
            alignItems={{ md: 'alignItemsFlexEnd' }}
            fullWidth={{ default: 'fullWidth' }}
          >
            <FormField
              id="username-field"
              label={t`Username`}
              name="username"
              type="text"
              isDisabled={!config.me.is_superuser}
            />
            <PasswordField
              id="password-field"
              name="password"
              label={t`Password`}
              isDisabled={!config.me.is_superuser}
            />
            <Button
              aria-label={t`Get subscriptions`}
              ouiaId="subscription-modal-button"
              onClick={toggleModal}
              style={{ maxWidth: 'fit-content' }}
              isDisabled={!(username.value && password.value)}
            >
              {t`Get subscription`}
            </Button>
            {isModalOpen && (
              <SubscriptionModal
                subscriptionCreds={{
                  username: username.value,
                  password: password.value,
                }}
                selectedSubscription={subscription?.value}
                onClose={closeModal}
                onConfirm={(value) => subscriptionHelpers.setValue(value)}
              />
            )}
          </Flex>
          {subscription.value && (
            <Flex
              id="selected-subscription"
              alignSelf={{ default: 'alignSelfFlexStart' }}
              spaceItems={{ default: 'spaceItemsMd' }}
            >
              <b>{t`Selected`}</b>
              <FlexItem>
                <i>{subscription?.value?.subscription_name}</i>
                <Tooltip
                  trigger="mouseenter focus click"
                  content={t`Clear subscription`}
                >
                  <Button
                    onClick={() => subscriptionHelpers.setValue(null)}
                    variant="plain"
                    aria-label={t`Clear subscription selection`}
                    ouiaId="clear-subscription-selection"
                  >
                    <TimesIcon />
                  </Button>
                </Tooltip>
              </FlexItem>
            </Flex>
          )}
        </>
      )}
    </Flex>
  );
}
export default SubscriptionStep;
