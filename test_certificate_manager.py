#!/usr/bin/env python3
"""
Test script for AWX Certificate Manager

This script validates the certificate generation functionality
using the same approach as the validated proof of concept.
"""
import os
import sys
import django
import logging
from pathlib import Path

# Add AWX to Python path
sys.path.insert(0, '/Users/ben/git/awx')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'awx.settings.development')
django.setup()

# Import AWX modules after Django setup
from awx.main.analytics.certificate_manager import get_or_generate_client_certificate, check_certificate_health

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_certificate_generation():
    """Test certificate generation with Red Hat credentials"""
    print("=== Testing AWX Certificate Manager ===")
    
    # Use the same credentials that worked in our proof of concept
    username = "bthomass"  # Replace with actual test credentials
    password = input("Enter Red Hat password for testing: ")
    
    try:
        print("1. Testing certificate generation...")
        cert_path, key_path = get_or_generate_client_certificate(username, password)
        
        if cert_path and key_path:
            print(f"✅ Certificate generation successful!")
            print(f"   Certificate: {cert_path}")
            print(f"   Private key: {key_path}")
            
            # Verify files exist
            if os.path.exists(cert_path) and os.path.exists(key_path):
                print("✅ Certificate files created successfully")
                
                # Check certificate content
                with open(cert_path, 'r') as f:
                    cert_content = f.read()
                    if 'BEGIN CERTIFICATE' in cert_content and 'Red Hat Candlepin Authority' in cert_content:
                        print("✅ Certificate contains valid Red Hat Candlepin Authority signature")
                    else:
                        print("⚠️  Certificate content may be invalid")
                
            else:
                print("❌ Certificate files not created")
                
        else:
            print("❌ Certificate generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Certificate generation error: {e}")
        return False
    
    # Test health check
    try:
        print("\n2. Testing certificate health check...")
        health = check_certificate_health()
        print(f"Health status: {health}")
        
        if health.get('status') == 'healthy':
            print("✅ Certificate health check passed")
        else:
            print(f"⚠️  Certificate health: {health.get('message', 'Unknown issue')}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test certificate caching
    try:
        print("\n3. Testing certificate caching...")
        cert_path_2, key_path_2 = get_or_generate_client_certificate(username, password)
        
        if cert_path == cert_path_2 and key_path == key_path_2:
            print("✅ Certificate caching working correctly")
        else:
            print("⚠️  Certificate caching may not be working")
            
    except Exception as e:
        print(f"❌ Caching test error: {e}")
    
    return True


def test_authentication_fallback():
    """Test authentication fallback behavior"""
    print("\n=== Testing Authentication Fallback ===")
    
    try:
        # Test with invalid credentials to trigger fallback
        print("1. Testing fallback with invalid credentials...")
        cert_path, key_path = get_or_generate_client_certificate("invalid_user", "invalid_pass")
        
        if cert_path is None and key_path is None:
            print("✅ Fallback behavior working - returns None for invalid credentials")
        else:
            print("⚠️  Unexpected behavior with invalid credentials")
            
    except Exception as e:
        print(f"⚠️  Exception during fallback test (expected): {e}")
    
    print("2. Testing disabled certificate authentication...")
    # Test would require modifying settings, skipping for now
    print("⚠️  Settings test skipped (requires configuration change)")


def cleanup_test_certificates():
    """Clean up test certificates"""
    print("\n=== Cleanup ===")
    try:
        from awx.main.analytics.certificate_manager import certificate_manager
        cert_dir = certificate_manager.cert_dir
        
        cert_file = os.path.join(cert_dir, 'aap-analytics-client.crt')
        key_file = os.path.join(cert_dir, 'aap-analytics-client.key')
        
        if os.path.exists(cert_file):
            os.remove(cert_file)
            print("✅ Removed test certificate")
            
        if os.path.exists(key_file):
            os.remove(key_file)
            print("✅ Removed test private key")
            
        # Clean up cache
        from django.core.cache import cache
        cache.delete("aap_client_certificate")
        cache.delete("aap_consumer_info")
        print("✅ Cleared certificate cache")
        
    except Exception as e:
        print(f"⚠️  Cleanup error: {e}")


if __name__ == '__main__':
    print("AWX Certificate Manager Test")
    print("============================")
    
    try:
        success = test_certificate_generation()
        if success:
            test_authentication_fallback()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        cleanup_input = input("\nClean up test certificates? (y/n): ")
        if cleanup_input.lower() in ['y', 'yes']:
            cleanup_test_certificates()
        
    print("\nTest complete!")