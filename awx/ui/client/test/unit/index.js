// Import angular and angular-mocks to the global scope
import 'angular';
import 'angular-mocks';
import 'angular-gettext';
import 'angular-ui-router';

// Import custom Angular module dependencies
import '../../src/i18n';
import '../../lib/services';
import '../../lib/components';
import '../../lib/models';

// Import tests
import './panel-body.spec';
import './layout.spec';
import './side-nav.spec';
