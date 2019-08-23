import Base from '../Base';

class AdHocCommands extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/ad_hoc_commands/';
  }
}

export default AdHocCommands;
