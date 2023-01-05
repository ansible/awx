import React, { useState } from 'react';
import { t } from '@lingui/macro';
import { Select, SelectOption, SelectVariant } from '@patternfly/react-core';

function RelatedLookupTypeInput({
  value,
  setValue,
  maxSelectHeight,
  enableFuzzyFiltering,
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Select
      ouiaId="set-lookup-typeahead"
      aria-label={t`Related search type`}
      className="lookupSelect"
      variant={SelectVariant.typeahead}
      typeAheadAriaLabel={t`Related search type typeahead`}
      onToggle={setIsOpen}
      onSelect={(event, selection) => setValue(selection)}
      selections={value}
      isOpen={isOpen}
      placeholderText={t`Related search type`}
      maxHeight={maxSelectHeight}
      noResultsFoundText={t`No results found`}
    >
      <SelectOption
        id="name-option-select"
        key="name__icontains"
        value="name__icontains"
        description={t`Fuzzy search on name field.`}
      />
      <SelectOption
        id="name-exact-option-select"
        key="name"
        value="name"
        description={t`Exact search on name field.`}
      />
      <SelectOption
        id="id-option-select"
        key="id"
        value="id"
        description={t`Exact search on id field.`}
      />
      {enableFuzzyFiltering && (
        <SelectOption
          id="search-option-select"
          key="search"
          value="search"
          description={t`Fuzzy search on id, name or description fields.`}
        />
      )}
    </Select>
  );
}

export default RelatedLookupTypeInput;
