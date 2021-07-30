import React, { useState } from 'react';
import { string, oneOfType, arrayOf, func } from 'prop-types';
import { t } from '@lingui/macro';
import { Select, SelectOption, SelectVariant } from '@patternfly/react-core';

function Option({ show, ...props }) {
  if (!show) {
    return null;
  }
  return <SelectOption {...props} />;
}
Option.defaultProps = {
  show: true,
};

function LookupTypeInput({ value, type, setValue, maxSelectHeight }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Select
      ouiaId="set-lookup-typeahead"
      aria-label={t`Lookup select`}
      className="lookupSelect"
      variant={SelectVariant.typeahead}
      typeAheadAriaLabel={t`Lookup typeahead`}
      onToggle={setIsOpen}
      onSelect={(event, selection) => setValue(selection)}
      onClear={() => setValue(null)}
      selections={value}
      isOpen={isOpen}
      placeholderText={t`Lookup type`}
      maxHeight={maxSelectHeight}
      noResultsFoundText={t`No results found`}
    >
      <Option
        id="exact-option-select"
        key="exact"
        value="exact"
        description={t`Exact match (default lookup if not specified).`}
      />
      <Option
        id="iexact-option-select"
        key="iexact"
        value="iexact"
        description={t`Case-insensitive version of exact.`}
        show={type === 'string'}
      />
      <Option
        id="contains-option-select"
        key="contains"
        value="contains"
        description={t`Field contains value.`}
        show={type === 'string'}
      />
      <Option
        id="icontains-option-select"
        key="icontains"
        value="icontains"
        description={t`Case-insensitive version of contains`}
        show={type === 'string'}
      />
      <Option
        id="startswith-option-select"
        key="startswith"
        value="startswith"
        description={t`Field starts with value.`}
        show={type !== 'datetime'}
      />
      <Option
        id="istartswith-option-select"
        key="istartswith"
        value="istartswith"
        description={t`Case-insensitive version of startswith.`}
        show={type !== 'datetime'}
      />
      <Option
        id="endswith-option-select"
        key="endswith"
        value="endswith"
        description={t`Field ends with value.`}
        show={type !== 'datetime'}
      />
      <Option
        id="iendswith-option-select"
        key="iendswith"
        value="iendswith"
        description={t`Case-insensitive version of endswith.`}
        show={type !== 'datetime'}
      />
      <Option
        id="regex-option-select"
        key="regex"
        value="regex"
        description={t`Field matches the given regular expression.`}
      />
      <Option
        id="iregex-option-select"
        key="iregex"
        value="iregex"
        description={t`Case-insensitive version of regex.`}
      />
      <Option
        id="gt-option-select"
        key="gt"
        value="gt"
        description={t`Greater than comparison.`}
        show={type !== 'json'}
      />
      <Option
        id="gte-option-select"
        key="gte"
        value="gte"
        description={t`Greater than or equal to comparison.`}
        show={type !== 'json'}
      />
      <Option
        id="lt-option-select"
        key="lt"
        value="lt"
        description={t`Less than comparison.`}
        show={type !== 'json'}
      />
      <Option
        id="lte-option-select"
        key="lte"
        value="lte"
        description={t`Less than or equal to comparison.`}
        show={type !== 'json'}
      />
      <Option
        id="isnull-option-select"
        key="isnull"
        value="isnull"
        description={t`Check whether the given field or related object is null; expects a boolean value.`}
      />
      <Option
        id="in-option-select"
        key="in"
        value="in"
        description={t`Check whether the given field's value is present in the list provided; expects a comma-separated list of items.`}
      />
    </Select>
  );
}
LookupTypeInput.propTypes = {
  type: string,
  value: oneOfType([string, arrayOf(string)]),
  setValue: func.isRequired,
  maxSelectHeight: string,
};
LookupTypeInput.defaultProps = {
  type: 'string',
  value: '',
  maxSelectHeight: '300px',
};

export default LookupTypeInput;
