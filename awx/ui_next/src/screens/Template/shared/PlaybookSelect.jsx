import React, { useCallback, useEffect, useState } from 'react';
import { number, string, oneOfType } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import {
  Select as PFSelect,
  SelectVariant,
  SelectOption as PFSelectOption,
} from '@patternfly/react-core';
import { ProjectsAPI } from '../../../api';
import useRequest from '../../../util/useRequest';

const Select = styled(PFSelect)`
  ul {
    max-width: 495px;
  }
`;
const SelectOption = styled(PFSelectOption)`
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
`;
function PlaybookSelect({
  projectId,
  isValid,
  selected,
  onBlur,
  onError,
  onChange,
  i18n,
  helpers,
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
      maxHeight="100vh"
      noResultsFoundText={i18n._(t`No results found`)}
      variant={SelectVariant.typeahead}
      selections={selected}
      onToggle={() => {
        helpers.setTouched();
        setIsOpen(!isOpen);
      }}
      placeholderText={i18n._(t`Select a playbook`)}
      onSelect={(event, selection) => {
        setIsOpen(false);
        onChange(selection);
      }}
      id="template-playbook"
      isValid={isValid}
      onBlur={onBlur}
      onClear={() => {
        helpers.setTouched();
        onChange('');
      }}
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
