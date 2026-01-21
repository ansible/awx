"""
Django management command for AWX Analytics Certificate Management
"""
import logging
import json
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from awx.main.analytics.certificate_manager import (
    get_certificate_info,
    force_certificate_renewal,
    check_certificate_health,
    get_or_generate_client_certificate
)


class Command(BaseCommand):
    """
    Manage AWX analytics client certificates for authenticated metrics upload
    """

    help = 'Manage AWX analytics client certificates'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['status', 'renew', 'generate', 'health'],
            help='Action to perform: status (detailed info), renew (force renewal), generate (create new), health (health check)'
        )
        parser.add_argument(
            '--username', 
            dest='username',
            help='Red Hat username for certificate operations (if not provided, uses AWX settings)'
        )
        parser.add_argument(
            '--password',
            dest='password', 
            help='Red Hat password for certificate operations (if not provided, uses AWX settings)'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            dest='json_output',
            help='Output results in JSON format'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='Enable verbose logging'
        )

    def init_logging(self):
        """Initialize logging configuration"""
        self.logger = logging.getLogger('awx.main.analytics.certificates')
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def get_credentials(self, options):
        """Get Red Hat credentials from options or AWX settings"""
        username = options.get('username')
        password = options.get('password')
        
        if not username:
            username = getattr(settings, 'REDHAT_USERNAME', None)
            if not username:
                username = getattr(settings, 'SUBSCRIPTIONS_CLIENT_ID', None)
        
        if not password:
            password = getattr(settings, 'REDHAT_PASSWORD', None)
            if not password:
                password = getattr(settings, 'SUBSCRIPTIONS_CLIENT_SECRET', None)
        
        return username, password

    def handle_status(self, options):
        """Handle certificate status command"""
        self.logger.info("Retrieving certificate status...")
        
        cert_info = get_certificate_info()
        
        if options['json_output']:
            self.stdout.write(json.dumps(cert_info, indent=2))
        else:
            self.stdout.write("Analytics Certificate Status:")
            self.stdout.write(f"  Status: {cert_info.get('status', 'unknown')}")
            
            if cert_info.get('message'):
                self.stdout.write(f"  Message: {cert_info['message']}")
            
            if cert_info.get('cert_path'):
                self.stdout.write(f"  Certificate Path: {cert_info['cert_path']}")
                self.stdout.write(f"  Private Key Path: {cert_info.get('key_path', 'unknown')}")
            
            if cert_info.get('days_until_expiry') is not None:
                days = cert_info['days_until_expiry']
                self.stdout.write(f"  Days Until Expiry: {days}")
                if days <= 7:
                    self.stdout.write(self.style.WARNING("  ⚠️  Certificate expires soon!"))
                elif days <= 0:
                    self.stdout.write(self.style.ERROR("  ❌ Certificate has expired!"))
                else:
                    self.stdout.write(self.style.SUCCESS("  ✅ Certificate is valid"))
            
            if cert_info.get('consumer_uuid'):
                self.stdout.write(f"  Consumer UUID: {cert_info['consumer_uuid']}")
                self.stdout.write(f"  Consumer Name: {cert_info.get('consumer_name', 'unknown')}")
                self.stdout.write(f"  Organization: {cert_info.get('organization', 'unknown')}")
            
            self.stdout.write(f"  Needs Renewal: {'Yes' if cert_info.get('needs_renewal', True) else 'No'}")

    def handle_health(self, options):
        """Handle certificate health check command"""
        self.logger.info("Checking certificate health...")
        
        health = check_certificate_health()
        
        if options['json_output']:
            self.stdout.write(json.dumps(health, indent=2))
        else:
            status = health.get('status', 'unknown')
            message = health.get('message', 'No message')
            
            if status == 'healthy':
                self.stdout.write(self.style.SUCCESS(f"✅ Certificate Health: {status.upper()}"))
            elif status == 'warning':
                self.stdout.write(self.style.WARNING(f"⚠️  Certificate Health: {status.upper()}"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Certificate Health: {status.upper()}"))
            
            self.stdout.write(f"Message: {message}")
            
            if health.get('days_until_expiry') is not None:
                self.stdout.write(f"Days Until Expiry: {health['days_until_expiry']}")

    def handle_renew(self, options):
        """Handle certificate renewal command"""
        username, password = self.get_credentials(options)
        
        if not username or not password:
            raise CommandError("Red Hat credentials required. Provide --username/--password or configure AWX settings.")
        
        self.logger.info("Forcing certificate renewal...")
        
        success = force_certificate_renewal(username, password)
        
        if success:
            self.stdout.write(self.style.SUCCESS("✅ Certificate renewal successful"))
            
            # Show updated status
            if not options['json_output']:
                self.stdout.write("\nUpdated certificate status:")
                self.handle_status(options)
        else:
            raise CommandError("❌ Certificate renewal failed. Check logs for details.")

    def handle_generate(self, options):
        """Handle certificate generation command"""
        username, password = self.get_credentials(options)
        
        if not username or not password:
            raise CommandError("Red Hat credentials required. Provide --username/--password or configure AWX settings.")
        
        self.logger.info("Generating new certificate...")
        
        cert_path, key_path = get_or_generate_client_certificate(username, password)
        
        if cert_path and key_path:
            self.stdout.write(self.style.SUCCESS("✅ Certificate generation successful"))
            self.stdout.write(f"Certificate: {cert_path}")
            self.stdout.write(f"Private Key: {key_path}")
            
            # Show certificate info
            if not options['json_output']:
                self.stdout.write("\nCertificate details:")
                self.handle_status(options)
        else:
            raise CommandError("❌ Certificate generation failed. Check logs for details.")

    def handle(self, *args, **options):
        """Main command handler"""
        self.verbose = options.get('verbose', False)
        self.init_logging()
        
        action = options['action']
        
        # Check if certificate authentication is enabled
        if not getattr(settings, 'AWX_ANALYTICS_CERTIFICATE_AUTH_ENABLED', True):
            if options['json_output']:
                result = {"error": "Certificate authentication is disabled in AWX settings"}
                self.stdout.write(json.dumps(result, indent=2))
            else:
                self.stdout.write(self.style.WARNING("⚠️  Certificate authentication is disabled in AWX settings"))
                self.stdout.write("Set AWX_ANALYTICS_CERTIFICATE_AUTH_ENABLED = True to enable")
            return
        
        try:
            if action == 'status':
                self.handle_status(options)
            elif action == 'health':
                self.handle_health(options)
            elif action == 'renew':
                self.handle_renew(options)
            elif action == 'generate':
                self.handle_generate(options)
            else:
                raise CommandError(f"Unknown action: {action}")
                
        except Exception as e:
            if options['json_output']:
                error_result = {"error": str(e)}
                self.stdout.write(json.dumps(error_result, indent=2))
            else:
                self.logger.error(f"Command failed: {e}")
            raise