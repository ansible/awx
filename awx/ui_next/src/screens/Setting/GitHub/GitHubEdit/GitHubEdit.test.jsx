import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import GitHubEdit from './GitHubEdit';

describe('<GitHubEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<GitHubEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('GitHubEdit').length).toBe(1);
  });
});
