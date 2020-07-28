import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import UIEdit from './UIEdit';

describe('<UIEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<UIEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('UIEdit').length).toBe(1);
  });
});
