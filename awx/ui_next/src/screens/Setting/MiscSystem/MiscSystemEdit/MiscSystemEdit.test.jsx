import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import MiscSystemEdit from './MiscSystemEdit';

describe('<MiscSystemEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<MiscSystemEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('MiscSystemEdit').length).toBe(1);
  });
});
