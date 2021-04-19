import React from 'react';

import { t } from '@lingui/macro';
import { ChipGroup as PFChipGroup } from '@patternfly/react-core';
import { number } from 'prop-types';

function ChipGroup({ numChips, totalChips, ...props }) {
  return (
    <PFChipGroup
      {...props}
      numChips={numChips}
      expandedText={t`Show less`}
      collapsedText={t`${totalChips - numChips} more`}
    />
  );
}

ChipGroup.propTypes = {
  numChips: number.isRequired,
  totalChips: number.isRequired,
};

export default ChipGroup;
