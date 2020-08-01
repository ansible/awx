import React, { useCallback, useEffect } from 'react';
import { number, string, oneOfType } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import AnsibleSelect from '../../../components/AnsibleSelect';
import { ProjectsAPI } from '../../../api';
import useRequest from '../../../util/useRequest';

function PlaybookSelect({ projectId, isValid, field, onBlur, onError, i18n }) {
  const {
    result: options,
    request: fetchOptions,
    isLoading,
    error,
  } = useRequest(
    useCallback(async () => {
      if (!projectId) {
        return [];
      }
      const { data } = await ProjectsAPI.readPlaybooks(projectId);
      const opts = (data || []).map(playbook => ({
        value: playbook,
        key: playbook,
        label: playbook,
        isDisabled: false,
      }));

      opts.unshift({
        value: '',
        key: '',
        label: i18n._(t`Choose a playbook`),
        isDisabled: false,
      });
      return opts;
    }, [projectId, i18n]),
    []
  );

  useEffect(() => {
    fetchOptions();
  }, [fetchOptions]);

  useEffect(() => {
    if (error) {
      onError(error);
    }
  }, [error, onError]);

  return (
    <AnsibleSelect
      id="template-playbook"
      data={options}
      isValid={isValid}
      {...field}
      onBlur={onBlur}
      isDisabled={isLoading}
    />
  );
}
PlaybookSelect.propTypes = {
  projectId: oneOfType([number, string]),
};
PlaybookSelect.defaultProps = {
  projectId: null,
};

export { PlaybookSelect as _PlaybookSelect };
export default withI18n()(PlaybookSelect);
