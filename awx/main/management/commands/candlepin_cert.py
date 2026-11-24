import sys

from argparse import RawDescriptionHelpFormatter

from django.core.management.base import BaseCommand

from awx.main.utils.candlepin.client import CandlepinClient
from awx.main.utils.candlepin.lifecycle import (
    get_candlepin_ca,
    get_candlepin_url,
    get_proxy_url,
    get_renewal_days,
    needs_renewal,
    parse_cert,
)
from awx.main.utils.candlepin import (
    _fetch_candlepin_cert_from_db,
    _save_candlepin_cert_to_db,
    _save_candlepin_registration_to_db,
    resolve_registration_credentials,
)


class Command(BaseCommand):
    """
    Manage Candlepin consumer registration and certificate lifecycle.

    Subcommands:
      register  Register this AAP instance as a Candlepin consumer and obtain an
                identity certificate for mTLS analytics uploads.
      renew     Perform a manual check-in and, if needed, renew the stored identity
                certificate.
    """

    help = 'Manage Candlepin consumer registration and certificate lifecycle'

    def create_parser(self, prog_name, subcommand, **kwargs):
        return super().create_parser(
            prog_name,
            subcommand,
            formatter_class=RawDescriptionHelpFormatter,
            epilog='\n'.join(
                [
                    'SUBCOMMANDS',
                    '',
                    '  register  Register this instance as a Candlepin consumer.',
                    '            Credentials are read from AWX database by default',
                    '            (REDHAT_USERNAME, REDHAT_PASSWORD). The organization is',
                    '            discovered automatically from the Candlepin account.',
                    '            Pass --username / --password-stdin / --org to override.',
                    '            Example: echo "password" | awx-manage candlepin_cert register --username user --password-stdin',
                    '',
                    '  renew     Perform a manual check-in and proactive cert renewal.',
                    '            Reads the stored cert/key/UUID from database.',
                    '            Use --force to renew even if the cert is not near expiry.',
                    '',
                    'CONFIGURATION',
                    '',
                    '  Settings can be configured via Django settings (awx/settings/defaults.py):',
                    '',
                    '  AWX_ANALYTICS_CANDLEPIN_URL              Candlepin base URL',
                    '                                           (default: https://subscription.example.com/candlepin)',
                    '  AWX_ANALYTICS_CANDLEPIN_CA               Path to Candlepin CA cert for TLS verification',
                    '  AWX_ANALYTICS_CANDLEPIN_RENEWAL_THRESHOLD_DAYS  Days before expiry to trigger renewal (default: 90)',
                    '  AWX_ANALYTICS_CANDLEPIN_PROXY_URL        HTTP/HTTPS proxy for Candlepin API calls',
                ]
            ),
            **kwargs,
        )

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='subcommand', metavar='subcommand')
        subparsers.required = True

        # --- register ---
        reg = subparsers.add_parser(
            'register',
            help='Register this instance as a Candlepin consumer',
            formatter_class=RawDescriptionHelpFormatter,
        )
        reg.add_argument('--username', help='Red Hat subscription username (overrides REDHAT_USERNAME from database)')
        reg.add_argument(
            '--password-stdin', dest='password_stdin', action='store_true', help='Read password from stdin (overrides REDHAT_PASSWORD from database)'
        )
        reg.add_argument('--org', help='Candlepin owner/org key (overrides auto-discovered organization)')
        reg.add_argument('--candlepin-url', dest='candlepin_url', help='Candlepin base URL (overrides AWX_ANALYTICS_CANDLEPIN_URL setting)')
        reg.add_argument(
            '--candlepin-ca', dest='candlepin_ca', help='Path to Candlepin CA cert for TLS verification (overrides AWX_ANALYTICS_CANDLEPIN_CA setting)'
        )
        reg.add_argument('--proxy', help='HTTP/HTTPS proxy URL (overrides AWX_ANALYTICS_CANDLEPIN_PROXY_URL setting)')
        reg.add_argument('--no-verify-tls', dest='no_verify_tls', action='store_true', help='Disable TLS certificate verification for Candlepin API calls')
        reg.add_argument('--force', action='store_true', help='Re-register even if a certificate already exists in database')
        reg.add_argument('--dry-run', dest='dry_run', action='store_true', help='Perform registration but do not save the result to database')

        # --- renew ---
        ren = subparsers.add_parser(
            'renew',
            help='Check in and renew the Candlepin identity certificate',
            formatter_class=RawDescriptionHelpFormatter,
        )
        ren.add_argument('--candlepin-url', dest='candlepin_url', help='Candlepin base URL (overrides AWX_ANALYTICS_CANDLEPIN_URL setting)')
        ren.add_argument(
            '--candlepin-ca', dest='candlepin_ca', help='Path to Candlepin CA cert for TLS verification (overrides AWX_ANALYTICS_CANDLEPIN_CA setting)'
        )
        ren.add_argument('--proxy', help='HTTP/HTTPS proxy URL (overrides AWX_ANALYTICS_CANDLEPIN_PROXY_URL setting)')
        ren.add_argument('--no-verify-tls', dest='no_verify_tls', action='store_true', help='Disable TLS certificate verification for Candlepin API calls')
        ren.add_argument('--force', action='store_true', help='Renew the certificate even if it is not near expiry')
        ren.add_argument('--dry-run', dest='dry_run', action='store_true', help='Perform check-in and renewal but do not save the result to database')

    def handle(self, *args, **options):
        subcommand = options['subcommand']
        if subcommand == 'register':
            ok = self._handle_register(options)
        elif subcommand == 'renew':
            ok = self._handle_renew(options)
        else:
            self.stderr.write(f'Unknown subcommand: {subcommand}')
            sys.exit(1)

        if not ok:
            sys.exit(1)

    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------

    def _resolve_and_validate_credentials(self, options):
        """Merge CLI options with DB values and validate all required fields are present.

        Returns ``(username, password, org, db_install_uuid)`` on success, or ``None``
        if any required field is missing (errors are written to ``self.stderr``).
        """
        username_override = options.get('username')
        org_override = options.get('org')
        verify_tls = not options.get('no_verify_tls', False)

        # Read password from stdin if --password-stdin is set
        if options.get('password_stdin'):
            password_override = sys.stdin.read().strip()
            if not password_override:
                self.stderr.write('--password-stdin specified but no password provided on stdin')
                return None
        else:
            password_override = None

        # Use shared resolution and validation function
        username, password, org, install_uuid, errors = resolve_registration_credentials(
            username_override=username_override, password_override=password_override, org_override=org_override, verify_tls=verify_tls
        )

        if errors:
            for error in errors:
                self.stderr.write(f'Missing required value: {error}')
            return None

        return username, password, org, install_uuid

    def _handle_register(self, options):
        dry_run = options['dry_run']
        force = options['force']

        # Check whether a cert is already stored unless --force.
        existing_cert, existing_key, _ = _fetch_candlepin_cert_from_db()
        if existing_cert and existing_key and not force:
            self.stdout.write('A Candlepin identity certificate is already stored in database. Use --force to re-register and replace it.')
            return True

        # Resolve credentials: CLI flags take precedence over database.
        resolved = self._resolve_and_validate_credentials(options)
        if resolved is None:
            return False
        username, password, org, db_install_uuid = resolved

        candlepin_url = options.get('candlepin_url') or get_candlepin_url()
        candlepin_ca = options.get('candlepin_ca') or get_candlepin_ca()
        proxy = options.get('proxy') or get_proxy_url()
        verify_tls = not options.get('no_verify_tls', False)

        # If dry-run, display what would happen and exit early before any Candlepin operations
        if dry_run:
            self.stdout.write('[dry-run] Would register with Candlepin:')
            self.stdout.write(f'  URL           : {candlepin_url}')
            self.stdout.write(f'  Organization  : {org}')
            self.stdout.write(f'  Username      : {username}')
            self.stdout.write(f'  Install UUID  : {db_install_uuid}')
            if candlepin_ca:
                self.stdout.write(f'  CA cert       : {candlepin_ca}')
            if proxy:
                self.stdout.write(f'  Proxy         : {proxy}')
            self.stdout.write(f'  Verify TLS    : {verify_tls}')
            self.stdout.write('[dry-run] No Candlepin operations performed.')
            return True

        client = CandlepinClient(base_url=candlepin_url, candlepin_ca=candlepin_ca, proxy=proxy, verify_tls=verify_tls)

        self.stdout.write(f'Registering with Candlepin at {candlepin_url} (org={org}) ...')
        try:
            cert_pem, key_pem, consumer_uuid = client.register_consumer(username, password, org, install_uuid=db_install_uuid)
        except Exception as e:
            self.stderr.write(f'Registration failed: {e}')
            return False

        self.stdout.write('Registered successfully.')
        self.stdout.write(f'  Consumer UUID : {consumer_uuid}')

        # Save to database
        if _save_candlepin_registration_to_db(cert_pem, key_pem, consumer_uuid):
            self.stdout.write('Certificate, key, and consumer UUID saved to database.')
        else:
            self.stderr.write('Failed to save registration to database.')
            return False

        # Best-effort certificate metadata display
        try:
            info = parse_cert(cert_pem)
            self.stdout.write(f'  Cert serial   : {info["serial"]}')
            self.stdout.write(f'  Cert CN       : {info["cn"]}')
            self.stdout.write(f'  Valid until   : {info["not_after"]} ({info["days_remaining"]} days remaining)')
        except ValueError as e:
            self.stdout.write(f'Certificate metadata unavailable: {e}')

        return True

    # ------------------------------------------------------------------
    # renew
    # ------------------------------------------------------------------

    def _handle_renew(self, options):
        dry_run = options['dry_run']
        force = options['force']

        cert_pem, key_pem, consumer_uuid = _fetch_candlepin_cert_from_db()

        if not cert_pem or not key_pem:
            self.stderr.write('No Candlepin identity certificate found in database. Run the register subcommand first.')
            return False

        if not consumer_uuid:
            self.stderr.write('CANDLEPIN_CONSUMER_UUID is not set. Run the register subcommand first.')
            return False

        try:
            info = parse_cert(cert_pem)
            self.stdout.write('Current certificate:')
            self.stdout.write(f'  Serial        : {info["serial"]}')
            self.stdout.write(f'  CN            : {info["cn"]}')
            self.stdout.write(f'  Valid until   : {info["not_after"]} ({info["days_remaining"]} days remaining)')
        except ValueError as e:
            self.stdout.write('Current certificate:')
            self.stdout.write(f'  Certificate metadata unavailable: {e}')
            info = None

        candlepin_url = options.get('candlepin_url') or get_candlepin_url()
        candlepin_ca = options.get('candlepin_ca') or get_candlepin_ca()
        proxy = options.get('proxy') or get_proxy_url()
        verify_tls = not options.get('no_verify_tls', False)
        renewal_days = get_renewal_days()

        # Check if renewal is needed (without force, just check cert expiry locally)
        renewal_needed = force or needs_renewal(cert_pem, renewal_days)

        # If dry-run, display what would happen and exit early before any Candlepin operations
        if dry_run:
            self.stdout.write('[dry-run] Would perform the following operations:')
            self.stdout.write(f'  URL           : {candlepin_url}')
            self.stdout.write(f'  Consumer UUID : {consumer_uuid}')
            if candlepin_ca:
                self.stdout.write(f'  CA cert       : {candlepin_ca}')
            if proxy:
                self.stdout.write(f'  Proxy         : {proxy}')
            self.stdout.write(f'  Verify TLS    : {verify_tls}')
            self.stdout.write('  1. Check in with Candlepin')
            if renewal_needed:
                reason = 'forced via --force' if force else f'expiry within {renewal_days} days'
                self.stdout.write(f'  2. Renew certificate ({reason})')
            else:
                if info:
                    self.stdout.write(f'  2. No renewal needed ({info["days_remaining"]} days remaining, threshold: {renewal_days} days)')
                else:
                    self.stdout.write(f'  2. No renewal needed (threshold: {renewal_days} days)')
            self.stdout.write('[dry-run] No Candlepin operations performed.')
            return True

        client = CandlepinClient(base_url=candlepin_url, candlepin_ca=candlepin_ca, proxy=proxy, verify_tls=verify_tls)

        self.stdout.write(f'Checking in with Candlepin at {candlepin_url} (consumer={consumer_uuid}) ...')
        checkin_success = client.checkin(consumer_uuid, cert_pem, key_pem)

        if not checkin_success:
            self.stderr.write('Check-in with Candlepin failed. Unable to verify certificate status.')
            self.stderr.write('Certificate renewal may still be needed. Use --force to renew anyway, or check logs for details.')
            return False

        self.stdout.write('Check-in successful.')

        if not renewal_needed:
            if info:
                self.stdout.write(f'Certificate has {info["days_remaining"]} days remaining (renewal threshold: {renewal_days} days). No renewal needed.')
            else:
                self.stdout.write(f'Certificate renewal threshold is {renewal_days} days. No renewal needed.')
            return True

        reason = 'forced via --force' if force else f'expiry within {renewal_days} days'
        self.stdout.write(f'Renewing certificate ({reason}) ...')
        try:
            new_cert_pem, new_key_pem = client.regenerate_cert(consumer_uuid, cert_pem, key_pem)
        except Exception as e:
            self.stderr.write(f'Certificate renewal failed: {e}')
            return False

        self.stdout.write('Certificate renewed successfully.')

        # Save to database
        if _save_candlepin_cert_to_db(new_cert_pem, new_key_pem):
            self.stdout.write('Renewed certificate and key saved to database.')
        else:
            self.stderr.write('Failed to save renewed certificate to database.')
            return False

        # Best-effort certificate metadata display
        try:
            new_info = parse_cert(new_cert_pem)
            if info:
                self.stdout.write(f'  Old serial    : {info["serial"]}')
            self.stdout.write(f'  New serial    : {new_info["serial"]}')
            self.stdout.write(f'  Valid until   : {new_info["not_after"]} ({new_info["days_remaining"]} days remaining)')
        except ValueError as e:
            self.stdout.write(f'Certificate metadata unavailable: {e}')

        return True
