export const API_MAX_PAGE_SIZE = 200;
export const API_ROOT = '/api/v2/';

export const EVENT_START_TASK = 'playbook_on_task_start';
export const EVENT_START_PLAY = 'playbook_on_play_start';
export const EVENT_START_PLAYBOOK = 'playbook_on_start';
export const EVENT_STATS_PLAY = 'playbook_on_stats';

export const HOST_STATUS_KEYS = ['dark', 'failures', 'changed', 'ok', 'skipped'];

export const JOB_STATUS_COMPLETE = ['successful', 'failed', 'unknown'];
export const JOB_STATUS_INCOMPLETE = ['canceled', 'error'];
export const JOB_STATUS_UNSUCCESSFUL = ['failed'].concat(JOB_STATUS_INCOMPLETE);
export const JOB_STATUS_FINISHED = JOB_STATUS_COMPLETE.concat(JOB_STATUS_INCOMPLETE);

export const OUTPUT_ANSI_COLORMAP = {
    0: '#000',
    1: '#A00',
    2: '#080',
    3: '#F0AD4E',
    4: '#00A',
    5: '#A0A',
    6: '#0AA',
    7: '#AAA',
    8: '#555',
    9: '#F55',
    10: '#5F5',
    11: '#FF5',
    12: '#55F',
    13: '#F5F',
    14: '#5FF',
    15: '#FFF'
};
export const OUTPUT_ELEMENT_CONTAINER = '.at-Stdout-container';
export const OUTPUT_ELEMENT_TBODY = '#atStdoutResultTable';
export const OUTPUT_ELEMENT_LAST = '#atStdoutMenuLast';
export const OUTPUT_MAX_BUFFER_LENGTH = 1000;
export const OUTPUT_MAX_LAG = 120;
export const OUTPUT_NO_COUNT_JOB_TYPES = ['ad_hoc_command', 'system_job', 'inventory_update'];
export const OUTPUT_ORDER_BY = 'start_line';
export const OUTPUT_PAGE_CACHE = true;
export const OUTPUT_PAGE_LIMIT = 5;
export const OUTPUT_PAGE_SIZE = 50;
export const OUTPUT_SCROLL_DELAY = 100;
export const OUTPUT_SCROLL_THRESHOLD = 0.1;
export const OUTPUT_SEARCH_DOCLINK = 'https://docs.ansible.com/ansible-tower/latest/html/userguide/search_sort.html';
export const OUTPUT_SEARCH_FIELDS = ['changed', 'created', 'failed', 'host_name', 'stdout', 'task', 'role', 'playbook', 'play', 'start_line', 'end_line'];
export const OUTPUT_SEARCH_KEY_EXAMPLES = ['host_name:localhost', 'task:set', 'created:>=2000-01-01', 'start_line:>=9000'];
export const OUTPUT_EVENT_LIMIT = OUTPUT_PAGE_LIMIT * OUTPUT_PAGE_SIZE;

export const WS_PREFIX = 'ws';
