import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ConstructedInventoryGroups from './ConstructedInventoryGroups';

describe('<ConstructedInventoryGroups />', () => {
  test('initially renders successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ConstructedInventoryGroups />);
    });
    expect(wrapper.length).toBe(1);
    expect(wrapper.find('ConstructedInventoryGroups').length).toBe(1);
  });
});
