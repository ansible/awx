function inventoryManageCopyCtrl($state) {
  var vm = this;
    
  var cancelPanel = function() {
    $state.go('inventoryManage', {}, {
      reload: true
    })
  };

  angular.extend(vm, {
    cancelPanel: cancelPanel
  });
};

export default ['$state', inventoryManageCopyCtrl
];
