import Base from '../Base';
import RelaunchMixin from '../mixins/Relaunch.mixin';

class AdHocCommands extends RelaunchMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/ad_hoc_commands/';
  }
}

export default AdHocCommands;
