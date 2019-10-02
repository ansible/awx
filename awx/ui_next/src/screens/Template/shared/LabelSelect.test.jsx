import React from 'react';
import { mount } from 'enzyme';
import { LabelsAPI } from '@api';
import { sleep } from '@testUtils/testUtils';
import LabelSelect from './LabelSelect';

jest.mock('@api');

const options = [{ id: 1, name: 'one' }, { id: 2, name: 'two' }];

describe('<LabelSelect />', () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  test('should fetch labels', async () => {
    LabelsAPI.read.mockReturnValue({
      data: { results: options },
    });
    const wrapper = mount(<LabelSelect value={[]} />);
    await sleep(1);
    wrapper.update();

    expect(LabelsAPI.read).toHaveBeenCalledTimes(1);
    expect(wrapper.find('MultiSelect').prop('options')).toEqual(options);
  });

  test('should fetch two pages labels if present', async () => {
    LabelsAPI.read.mockReturnValueOnce({
      data: {
        results: options,
        next: '/foo?page=2',
      },
    });
    LabelsAPI.read.mockReturnValueOnce({
      data: {
        results: options,
      },
    });
    const wrapper = mount(<LabelSelect value={[]} />);
    await sleep(1);
    wrapper.update();

    expect(LabelsAPI.read).toHaveBeenCalledTimes(2);
    expect(wrapper.find('MultiSelect').prop('options')).toEqual([
      ...options,
      ...options,
    ]);
  });
});
