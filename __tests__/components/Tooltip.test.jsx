import React from 'react';
import { mount } from 'enzyme';
import Tooltip from '../../src/components/Tooltip';

describe('<Tooltip />', () => {
  let elem;
  let content;
  let mouseOverHandler;
  let mouseOutHandler;
  const child = (<span>foo</span>);
  const message = 'hi';

  test('initially renders without crashing', () => {
    elem = mount(
      <Tooltip message={message}>
        {child}
      </Tooltip>
    );
    expect(elem.length).toBe(1);
  });

  test('shows/hides with mouse over and leave', () => {
    elem = mount(
      <Tooltip message={message}>
        {child}
      </Tooltip>
    );
    mouseOverHandler = elem.find('.mouseOverHandler');
    mouseOutHandler = elem.find('.mouseOutHandler');
    expect(elem.state().isDisplayed).toBe(false);
    elem.update();
    content = elem.find('.pf-c-tooltip__content');
    expect(content.length).toBe(0);
    mouseOverHandler.props().onMouseOver();
    expect(elem.state().isDisplayed).toBe(true);
    elem.update();
    content = elem.find('.pf-c-tooltip__content');
    expect(content.length).toBe(1);
    mouseOutHandler.props().onMouseLeave();
    expect(elem.state().isDisplayed).toBe(false);
    elem.update();
    content = elem.find('.pf-c-tooltip__content');
    expect(content.length).toBe(0);
  });

  test('shows/hides with focus and blur', () => {
    elem = mount(
      <Tooltip message={message}>
        {child}
      </Tooltip>
    );
    mouseOverHandler = elem.find('.mouseOverHandler');
    mouseOutHandler = elem.find('.mouseOutHandler');
    expect(elem.state().isDisplayed).toBe(false);
    elem.update();
    content = elem.find('.pf-c-tooltip__content');
    expect(content.length).toBe(0);
    mouseOverHandler.props().onFocus();
    expect(elem.state().isDisplayed).toBe(true);
    elem.update();
    content = elem.find('.pf-c-tooltip__content');
    expect(content.length).toBe(1);
    mouseOutHandler.props().onBlur();
    expect(elem.state().isDisplayed).toBe(false);
    elem.update();
    content = elem.find('.pf-c-tooltip__content');
    expect(content.length).toBe(0);
  });
});
