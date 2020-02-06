import React from 'react';
import { mount } from 'enzyme';
import NodeNextButton from './NodeNextButton';

const activeStep = {
  name: 'Node Type',
  key: 'node_resource',
  enableNext: true,
  component: {},
  id: 1,
};
const buttonText = 'Next';
const onClick = jest.fn();
const onNext = jest.fn();
const triggerNext = 0;
let wrapper;

describe('NodeNextButton', () => {
  beforeAll(() => {
    wrapper = mount(
      <NodeNextButton
        activeStep={activeStep}
        buttonText={buttonText}
        onClick={onClick}
        onNext={onNext}
        triggerNext={triggerNext}
      />
    );
  });

  afterAll(() => {
    wrapper.unmount();
  });

  test('Button text matches', () => {
    expect(wrapper.find('button').text()).toBe(buttonText);
  });

  test('Clicking button makes expected callback', () => {
    wrapper.find('button').simulate('click');
    expect(onClick).toBeCalledWith(activeStep);
  });

  test('onNext triggered when triggerNext counter incrimented', () => {
    wrapper.setProps({ triggerNext: 1 });
    expect(onNext).toBeCalled();
  });
});
