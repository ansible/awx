import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ConstructedInventoryAdd from './ConstructedInventoryAdd';

describe('<ConstructedInventoryAdd />', () => {
  test('initially renders successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ConstructedInventoryAdd />);
    });
    expect(wrapper.length).toBe(1);
    expect(wrapper.find('ConstructedInventoryAdd').length).toBe(1);
  });
});
