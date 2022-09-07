export const SELECTOR = '#chart';
export const PARENTSELECTOR = '.mesh-svg';
export const CHILDSELECTOR = '.mesh';
export const DEFAULT_RADIUS = 16;
export const MESH_FORCE_LAYOUT = {
  defaultCollisionFactor: DEFAULT_RADIUS * 2 + 30,
  defaultForceStrength: -50,
  defaultForceBody: 15,
  defaultForceX: 0,
  defaultForceY: 0,
};
export const DEFAULT_NODE_COLOR = 'white';
export const DEFAULT_NODE_HIGHLIGHT_COLOR = '#eee';
export const DEFAULT_NODE_LABEL_TEXT_COLOR = 'white';
export const DEFAULT_NODE_SYMBOL_TEXT_COLOR = 'black';
export const DEFAULT_NODE_STROKE_COLOR = '#ccc';
export const DEFAULT_FONT_SIZE = '12px';
export const LABEL_TEXT_MAX_LENGTH = 15;
export const MARGIN = 15;
export const NODE_STATE_COLOR_KEY = {
  ready: '#3E8635',
  'provision-fail': '#C9190B',
  'deprovision-fail': '#C9190B',
  unavailable: '#C9190B',
  installed: '#0066CC',
  provisioning: '#666',
  deprovisioning: '#666',
};

export const NODE_TYPE_SYMBOL_KEY = {
  hop: 'h',
  execution: 'Ex',
  hybrid: 'Hy',
  control: 'C',
};

export const ICONS = {
  clock:
    'M256 8C119 8 8 119 8 256s111 248 248 248 248-111 248-248S393 8 256 8zm0 448c-110.5 0-200-89.5-200-200S145.5 56 256 56s200 89.5 200 200-89.5 200-200 200zm61.8-104.4l-84.9-61.7c-3.1-2.3-4.9-5.9-4.9-9.7V116c0-6.6 5.4-12 12-12h32c6.6 0 12 5.4 12 12v141.7l66.8 48.6c5.4 3.9 6.5 11.4 2.6 16.8L334.6 349c-3.9 5.3-11.4 6.5-16.8 2.6z',
  checkmark:
    'M173.898 439.404l-166.4-166.4c-9.997-9.997-9.997-26.206 0-36.204l36.203-36.204c9.997-9.998 26.207-9.998 36.204 0L192 312.69 432.095 72.596c9.997-9.997 26.207-9.997 36.204 0l36.203 36.204c9.997 9.997 9.997 26.206 0 36.204l-294.4 294.401c-9.998 9.997-26.207 9.997-36.204-.001z',
  exclaimation:
    'M176 432c0 44.112-35.888 80-80 80s-80-35.888-80-80 35.888-80 80-80 80 35.888 80 80zM25.26 25.199l13.6 272C39.499 309.972 50.041 320 62.83 320h66.34c12.789 0 23.331-10.028 23.97-22.801l13.6-272C167.425 11.49 156.496 0 142.77 0H49.23C35.504 0 24.575 11.49 25.26 25.199z',
  minus:
    'M416 208H32c-17.67 0-32 14.33-32 32v32c0 17.67 14.33 32 32 32h384c17.67 0 32-14.33 32-32v-32c0-17.67-14.33-32-32-32z',
  plus: 'M416 208H272V64c0-17.67-14.33-32-32-32h-32c-17.67 0-32 14.33-32 32v144H32c-17.67 0-32 14.33-32 32v32c0 17.67 14.33 32 32 32h144v144c0 17.67 14.33 32 32 32h32c17.67 0 32-14.33 32-32V304h144c17.67 0 32-14.33 32-32v-32c0-17.67-14.33-32-32-32z',
};
