const getTabName = (tab) => {
  let tabName = '';
  if (tab === 'details') {
    tabName = 'Details';
  } else if (tab === 'access') {
    tabName = 'Access';
  } else if (tab === 'teams') {
    tabName = 'Teams';
  } else if (tab === 'notifications') {
    tabName = 'Notifications';
  }
  return tabName;
};

export default getTabName;
