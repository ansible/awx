import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import SettingList from './SettingList';

jest.mock('../../api');
jest.mock('hooks/useBrandName', () => ({
  __esModule: true,
  default: () => ({
    current: 'AWX',
  }),
}));

describe('<SettingList />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<SettingList />);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.length).toBe(1);
  });
});
