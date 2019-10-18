import React, { useState, useEffect } from 'react';
import { number, string, oneOfType } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import AnsibleSelect from '@components/AnsibleSelect';
import { ProjectsAPI } from '@api';

function PlaybookSelect({
  projectId,
  isValid,
  form,
  field,
  onBlur,
  onError,
  i18n,
}) {
  const [options, setOptions] = useState([]);
  useEffect(() => {
    if (!projectId) {
      return;
    }
    (async () => {
      try {
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
        setOptions(opts);
      } catch (contentError) {
        onError(contentError);
      }
    })();
  }, [projectId]);

  return (
    <AnsibleSelect
      id="template-playbook"
      data={options}
      isValid={isValid}
      form={form}
      {...field}
      onBlur={onBlur}
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
