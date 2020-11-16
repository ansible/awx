import React from 'react';
import { act } from 'react-dom/test-utils';
import { mount } from 'enzyme';
import { LabelsAPI } from '../../../api';
import LabelSelect from './LabelSelect';

jest.mock('../../../api');

const options = [
  { id: 1, name: 'one' },
  { id: 2, name: 'two' },
];

describe('<LabelSelect />', () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  test('should fetch labels', async () => {
    LabelsAPI.read.mockReturnValue({
      data: { results: options },
    });
    let wrapper;
    await act(async () => {
      wrapper = mount(
        <LabelSelect value={[]} onError={() => {}} onChange={() => {}} />
      );
    });
    expect(LabelsAPI.read).toHaveBeenCalledTimes(1);
    wrapper.find('SelectToggle').simulate('click');
    const selectOptions = wrapper.find('SelectOption');
    expect(selectOptions).toHaveLength(2);
    expect(selectOptions.at(0).prop('value')).toEqual(options[0]);
    expect(selectOptions.at(1).prop('value')).toEqual(options[1]);
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
        results: [
          { id: 3, name: 'three' },
          { id: 4, name: 'four' },
        ],
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mount(
        <LabelSelect value={[]} onError={() => {}} onChange={() => {}} />
      );
    });
    wrapper.update();

    expect(LabelsAPI.read).toHaveBeenCalledTimes(2);
    wrapper.find('SelectToggle').simulate('click');
    const selectOptions = wrapper.find('SelectOption');
    expect(selectOptions).toHaveLength(4);
  });
  test('Generate a label  ', async () => {
    let wrapper;
    const onChange = jest.fn();
    LabelsAPI.read.mockReturnValueOnce({
      data: {
        options,
      },
    });
    await act(async () => {
      wrapper = mount(
        <LabelSelect value={[]} onError={() => {}} onChange={onChange} />
      );
    });
    await wrapper.find('Select').invoke('onSelect')({}, 'foo');
    expect(onChange).toBeCalledWith([{ id: 'foo', name: 'foo' }]);
  });
});
