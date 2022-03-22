import * as d3 from 'd3';
import { truncateString } from '../../../util/strings';

import {
  NODE_STATE_COLOR_KEY,
  NODE_STATE_HTML_ENTITY_KEY,
  NODE_TYPE_SYMBOL_KEY,
  LABEL_TEXT_MAX_LENGTH,
} from '../constants';

export function getWidth(selector) {
  return selector ? d3.select(selector).node().clientWidth : 700;
}

export function getHeight(selector) {
  return selector ? d3.select(selector).node().clientHeight : 600;
}

export function renderStateColor(nodeState) {
  return NODE_STATE_COLOR_KEY[nodeState] ? NODE_STATE_COLOR_KEY[nodeState] : '';
}

export function renderLabelText(nodeState, name) {
  if (typeof nodeState === 'string' && typeof name === 'string') {
    return NODE_STATE_HTML_ENTITY_KEY[nodeState]
      ? `${NODE_STATE_HTML_ENTITY_KEY[nodeState]} ${truncateString(
          name,
          LABEL_TEXT_MAX_LENGTH
        )}`
      : ` ${truncateString(name, LABEL_TEXT_MAX_LENGTH)}`;
  }
  return ``;
}

export function renderNodeType(nodeType) {
  return NODE_TYPE_SYMBOL_KEY[nodeType] ? NODE_TYPE_SYMBOL_KEY[nodeType] : ``;
}

export function renderNodeIcon(selectedNode) {
  if (selectedNode) {
    const { node_type: nodeType } = selectedNode;
    return NODE_TYPE_SYMBOL_KEY[nodeType] ? NODE_TYPE_SYMBOL_KEY[nodeType] : ``;
  }
  return false;
}

export function redirectToDetailsPage(selectedNode, history) {
  if (selectedNode && history) {
    const { id: nodeId } = selectedNode;
    const constructedURL = `/instances/${nodeId}/details`;
    history.push(constructedURL);
  }
  return false;
}

// DEBUG TOOLS
export function getRandomInt(min, max) {
  min = Math.ceil(min);
  max = Math.floor(max);
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

const generateRandomLinks = (n, r) => {
  const links = [];
  for (let i = 0; i < r; i++) {
    const link = {
      source: n[getRandomInt(0, n.length - 1)].hostname,
      target: n[getRandomInt(0, n.length - 1)].hostname,
    };
    links.push(link);
  }
  return { nodes: n, links };
};

export const generateRandomNodes = (n) => {
  const nodes = [];
  function getRandomType() {
    return ['hybrid', 'execution', 'control', 'hop'][getRandomInt(0, 3)];
  }
  function getRandomState() {
    return ['healthy', 'error', 'disabled'][getRandomInt(0, 2)];
  }
  for (let i = 0; i < n; i++) {
    const id = i + 1;
    const randomType = getRandomType();
    const randomState = getRandomState();
    const node = {
      id,
      hostname: `node-${id}`,
      node_type: randomType,
      node_state: randomState,
    };
    nodes.push(node);
  }
  return generateRandomLinks(nodes, getRandomInt(1, n - 1));
};
