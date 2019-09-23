import React from 'react';
import { shallow } from 'enzyme';
import CollapsibleSection from './CollapsibleSection';

describe('<CollapsibleSection>', () => {
  it('should render contents', () => {
    const wrapper = shallow(
      <CollapsibleSection label="Advanced">foo</CollapsibleSection>
    );
    expect(wrapper.find('Button > *').prop('isExpanded')).toEqual(false);
    expect(wrapper.find('ExpandingContainer').prop('isExpanded')).toEqual(
      false
    );
    expect(wrapper.find('ExpandingContainer').prop('children')).toEqual('foo');
  });

  it('should toggle when clicked', () => {
    const wrapper = shallow(
      <CollapsibleSection label="Advanced">foo</CollapsibleSection>
    );
    expect(wrapper.find('Button > *').prop('isExpanded')).toEqual(false);
    wrapper.find('Button').simulate('click');
    expect(wrapper.find('Button > *').prop('isExpanded')).toEqual(true);
    expect(wrapper.find('ExpandingContainer').prop('isExpanded')).toEqual(true);
  });
});
