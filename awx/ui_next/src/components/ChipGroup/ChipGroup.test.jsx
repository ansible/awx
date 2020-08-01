import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ChipGroup from './ChipGroup';

describe('ChipGroup', () => {
  test('should mount properly', () => {
    const wrapper = mountWithContexts(
      <ChipGroup numChips={5} totalChips={10} />
    );
    expect(
      wrapper
        .find('ChipGroup')
        .at(1)
        .props().collapsedText
    ).toEqual('5 more');
  });
});
