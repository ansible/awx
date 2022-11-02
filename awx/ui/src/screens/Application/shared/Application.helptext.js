import { t } from '@lingui/macro';

const applicationHelpTextStrings = () => ({
  authorizationGrantType: t`The Grant type the user must use to acquire tokens for this application`,
  clientType: t`Set to Public or Confidential depending on how secure the client device is.`,
  redirectURIS: t`Allowed URIs list, space separated`,
});

export default applicationHelpTextStrings;
