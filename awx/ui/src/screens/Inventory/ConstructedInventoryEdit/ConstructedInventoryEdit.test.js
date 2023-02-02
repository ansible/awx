import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ConstructedInventoryEdit from './ConstructedInventoryEdit';

describe('<ConstructedInventoryEdit />', () => {
  test('initially renders successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ConstructedInventoryEdit />);
    });
    expect(wrapper.length).toBe(1);
    expect(wrapper.find('ConstructedInventoryEdit').length).toBe(1);
  });
});
