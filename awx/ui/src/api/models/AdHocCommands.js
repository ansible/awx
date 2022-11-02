import Base from '../Base';
import RunnableMixin from '../mixins/Runnable.mixin';

class AdHocCommands extends RunnableMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/ad_hoc_commands/';
  }

  readCredentials(id) {
    return this.http.get(`${this.baseUrl}${id}/credentials/`);
  }
}

export default AdHocCommands;
