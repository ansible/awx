import {
  renderStateColor,
  renderLabelText,
  renderNodeType,
  renderNodeIcon,
  renderLabelIcons,
  renderIconPosition,
  renderLinkState,
  redirectToDetailsPage,
  getHeight,
  getWidth,
} from './helpers';

import { ICONS } from '../constants';

describe('renderStateColor', () => {
  test('returns correct node state color', () => {
    expect(renderStateColor('ready')).toBe('#3E8635');
  });
  test('returns empty string if state is not found', () => {
    expect(renderStateColor('foo')).toBe('');
  });
  test('returns empty string if state is null', () => {
    expect(renderStateColor(null)).toBe('');
  });
  test('returns empty string if state is zero/integer', () => {
    expect(renderStateColor(0)).toBe('');
  });
});
describe('renderNodeType', () => {
  test('returns correct node type', () => {
    expect(renderNodeType('control')).toBe('C');
  });
  test('returns empty string if type is not found', () => {
    expect(renderNodeType('foo')).toBe('');
  });
  test('returns empty string if type is null', () => {
    expect(renderNodeType(null)).toBe('');
  });
  test('returns empty string if type is zero/integer', () => {
    expect(renderNodeType(0)).toBe('');
  });
});
describe('renderNodeIcon', () => {
  test('returns correct node icon', () => {
    expect(renderNodeIcon({ node_type: 'control' })).toBe('C');
  });
  test('returns empty string if state is not found', () => {
    expect(renderNodeIcon('foo')).toBe('');
  });
  test('returns false if state is null', () => {
    expect(renderNodeIcon(null)).toBe(false);
  });
  test('returns false if state is zero/integer', () => {
    expect(renderNodeIcon(0)).toBe(false);
  });
});
describe('renderLabelIcons', () => {
  test('returns correct label icon', () => {
    expect(renderLabelIcons('ready')).toBe(ICONS['checkmark']);
  });
  test('returns empty string if state is not found', () => {
    expect(renderLabelIcons('foo')).toBe('');
  });
  test('returns false if state is null', () => {
    expect(renderLabelIcons(null)).toBe(false);
  });
  test('returns false if state is zero/integer', () => {
    expect(renderLabelIcons(0)).toBe(false);
  });
});
describe('renderIconPosition', () => {
  const bbox = { x: 400, y: 400, width: 10, height: 20 };
  test('returns correct label icon', () => {
    expect(renderIconPosition('ready', bbox)).toBe(
      `translate(${bbox.x - 4.5}, ${bbox.y - 4.5}), scale(0.02)`
    );
  });
  test('returns empty string if state is not found', () => {
    expect(renderIconPosition('foo', bbox)).toBe('');
  });
  test('returns false if state is null', () => {
    expect(renderIconPosition(null)).toBe(false);
  });
  test('returns false if state is zero/integer', () => {
    expect(renderIconPosition(0)).toBe(false);
  });
});
describe('renderLinkState', () => {
  test('returns correct link state', () => {
    expect(renderLinkState('adding')).toBe(3);
  });
  test('returns null string if state is not found', () => {
    expect(renderLinkState('foo')).toBe(null);
  });
  test('returns null if state is null', () => {
    expect(renderLinkState(null)).toBe(null);
  });
  test('returns null if state is zero/integer', () => {
    expect(renderLinkState(0)).toBe(null);
  });
});
describe('getWidth', () => {
  test('returns 700 if selector is null', () => {
    expect(getWidth(null)).toBe(700);
  });
  test('returns 700 if selector is zero/integer', () => {
    expect(getWidth(0)).toBe(700);
  });
});
describe('getHeight', () => {
  test('returns 600 if selector is null', () => {
    expect(getHeight(null)).toBe(600);
  });
  test('returns 600 if selector is zero/integer', () => {
    expect(getHeight(0)).toBe(600);
  });
});
describe('renderLabelText', () => {
  test('returns label text correctly', () => {
    expect(renderLabelText('error', 'foo')).toBe('foo');
  });
  test('returns label text if invalid node state is passed', () => {
    expect(renderLabelText('foo', 'bar')).toBe('bar');
  });
  test('returns empty string if non string params are passed', () => {
    expect(renderLabelText(0, null)).toBe('');
  });
});
describe('redirectToDetailsPage', () => {
  test('returns false if incorrect params are passed', () => {
    expect(redirectToDetailsPage(null, 0)).toBe(false);
  });
});
