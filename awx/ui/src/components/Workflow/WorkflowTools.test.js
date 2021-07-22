import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import WorkflowTools from './WorkflowTools';

describe('WorkflowTools', () => {
  test('renders the expected content', () => {
    const wrapper = mountWithContexts(
      <WorkflowTools
        onClose={() => {}}
        onFitGraph={() => {}}
        onPan={() => {}}
        onPanToMiddle={() => {}}
        onZoomChange={() => {}}
        zoomPercentage={100}
      />
    );
    expect(wrapper).toHaveLength(1);
  });
  test('clicking zoom/pan buttons passes callback correct values', () => {
    const pan = jest.fn();
    const zoomChange = jest.fn();
    const wrapper = mountWithContexts(
      <WorkflowTools
        onClose={() => {}}
        onFitGraph={() => {}}
        onPan={pan}
        onPanToMiddle={() => {}}
        onZoomChange={zoomChange}
        zoomPercentage={95.7}
      />
    );
    wrapper.find('PlusIcon').simulate('click');
    expect(zoomChange).toHaveBeenCalledWith(1.1);
    wrapper.find('MinusIcon').simulate('click');
    expect(zoomChange).toHaveBeenCalledWith(0.8);
    wrapper.find('CaretLeftIcon').simulate('click');
    expect(pan).toHaveBeenCalledWith('left');
    wrapper.find('CaretUpIcon').simulate('click');
    expect(pan).toHaveBeenCalledWith('up');
    wrapper.find('CaretRightIcon').simulate('click');
    expect(pan).toHaveBeenCalledWith('right');
    wrapper.find('CaretDownIcon').simulate('click');
    expect(pan).toHaveBeenCalledWith('down');
  });
});
