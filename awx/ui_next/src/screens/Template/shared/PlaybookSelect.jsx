import React, { useCallback, useEffect, useState } from 'react';
import { number, string, oneOfType } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { SelectVariant, Select, SelectOption } from '@patternfly/react-core';
import { ProjectsAPI } from '../../../api';
import useRequest from '../../../util/useRequest';

function PlaybookSelect({
  projectId,
  isValid,
  selected,
  onBlur,
  onError,
  onChange,
  i18n,
}) {
  const [isDisabled, setIsDisabled] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
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

      return data;
    }, [projectId]),
    []
  );

  useEffect(() => {
    fetchOptions();
  }, [fetchOptions]);

  useEffect(() => {
    if (error) {
      if (error.response.status === 403) {
        setIsDisabled(true);
      } else {
        onError(error);
      }
    }
  }, [error, onError]);

  return (
    <Select
      ouiaId="JobTemplateForm-playbook"
      isOpen={isOpen}
      variant={SelectVariant.typeahead}
      selections={selected}
      onToggle={setIsOpen}
      placeholderText={i18n._(t`Select a playbook`)}
      isCreateable={false}
      onSelect={(event, value) => {
        onChange(value);
      }}
      id="template-playbook"
      isValid={isValid}
      onBlur={onBlur}
      isDisabled={isLoading || isDisabled}
    >
      {options.map(opt => (
        <SelectOption key={opt} value={opt} />
      ))}
    </Select>
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
