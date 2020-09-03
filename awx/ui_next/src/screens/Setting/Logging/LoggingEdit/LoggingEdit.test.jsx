import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import LoggingEdit from './LoggingEdit';

describe('<LoggingEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<LoggingEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('LoggingEdit').length).toBe(1);
  });
});
