import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import TACACSEdit from './TACACSEdit';

describe('<TACACSEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<TACACSEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('TACACSEdit').length).toBe(1);
  });
});
