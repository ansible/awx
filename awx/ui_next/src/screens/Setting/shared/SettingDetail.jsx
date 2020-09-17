import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Detail } from '../../../components/DetailList';
import { VariablesDetail } from '../../../components/CodeMirrorInput';

export default withI18n()(({ i18n, label, type, value }) => {
  const dataType = value === '$encrypted$' ? 'encrypted' : type;
  let detail = null;

  switch (dataType) {
    case 'nested object':
      detail = (
        <VariablesDetail
          label={label}
          rows={4}
          value={JSON.stringify(value || {}, undefined, 2)}
        />
      );
      break;
    case 'list':
      detail = <VariablesDetail rows={4} label={label} value={value} />;
      break;
    case 'image':
      detail = (
        <Detail
          alwaysVisible
          label={label}
          value={<img src={value} alt={label} height="40" width="40" />}
        />
      );
      break;
    case 'encrypted':
      detail = (
        <Detail
          alwaysVisible
          isEncrypted
          label={label}
          value={i18n._(t`Encrypted`)}
        />
      );
      break;
    case 'boolean':
      detail = (
        <Detail
          alwaysVisible
          label={label}
          value={value ? i18n._(t`On`) : i18n._(t`Off`)}
        />
      );
      break;
    case 'choice':
      detail = (
        <Detail
          alwaysVisible
          label={label}
          value={!value ? i18n._(t`Unconfigured`) : value}
          isUnconfigured={!value}
        />
      );
      break;
    case 'integer':
      detail = (
        <Detail
          alwaysVisible
          label={label}
          value={!value ? i18n._(t`Unconfigured`) : value}
          isUnconfigured={!value}
        />
      );
      break;
    case 'string':
      detail = (
        <Detail
          alwaysVisible
          label={label}
          value={!value ? i18n._(t`Unconfigured`) : value}
          isUnconfigured={!value}
        />
      );
      break;
    default:
      detail = null;
  }
  return detail;
});
