const ORDER = {
  minute: 1,
  hour: 2,
  day: 3,
  week: 4,
  month: 5,
  year: 6,
};

export default function sortFrequencies(a, b) {
  if (ORDER[a] < ORDER[b]) {
    return -1;
  }
  if (ORDER[a] > ORDER[b]) {
    return 1;
  }
  return 0;
}
