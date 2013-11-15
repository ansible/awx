import warnings
warnings.simplefilter('default')
warnings.warn("sync_media_s3 is deprecated and will be removed on march 2014; use sync_s3 instead.",
              PendingDeprecationWarning)


import datetime
import email
import mimetypes
from optparse import make_option
import os
import time
import gzip
try:
    from cStringIO import StringIO
    assert StringIO
except ImportError:
    from StringIO import StringIO


from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# Make sure boto is available
try:
    import boto
    import boto.exception
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


class Command(BaseCommand):
    # Extra variables to avoid passing these around
    AWS_ACCESS_KEY_ID = ''
    AWS_SECRET_ACCESS_KEY = ''
    AWS_BUCKET_NAME = ''
    AWS_CLOUDFRONT_DISTRIBUTION = ''
    SYNC_S3_RENAME_GZIP_EXT = ''

    DIRECTORY = ''
    FILTER_LIST = ['.DS_Store', '.svn', '.hg', '.git', 'Thumbs.db']
    GZIP_CONTENT_TYPES = (
        'text/css',
        'application/javascript',
        'application/x-javascript',
        'text/javascript'
    )

    uploaded_files = []
    upload_count = 0
    skip_count = 0

    option_list = BaseCommand.option_list + (
        make_option('-p', '--prefix',
                    dest='prefix',
                    default=getattr(settings, 'SYNC_MEDIA_S3_PREFIX', ''),
                    help="The prefix to prepend to the path on S3."),
        make_option('-d', '--dir',
                    dest='dir', default=settings.MEDIA_ROOT,
                    help="The root directory to use instead of your MEDIA_ROOT"),
        make_option('--gzip',
                    action='store_true', dest='gzip', default=False,
                    help="Enables gzipping CSS and Javascript files."),
        make_option('--renamegzip',
                    action='store_true', dest='renamegzip', default=False,
                    help="Enables renaming of gzipped assets to have '.gz' appended to the filename."),
        make_option('--expires',
                    action='store_true', dest='expires', default=False,
                    help="Enables setting a far future expires header."),
        make_option('--force',
                    action='store_true', dest='force', default=False,
                    help="Skip the file mtime check to force upload of all files."),
        make_option('--filter-list', dest='filter_list',
                    action='store', default='',
                    help="Override default directory and file exclusion filters. (enter as comma seperated line)"),
        make_option('--invalidate', dest='invalidate', default=False,
                    action='store_true',
                    help='Invalidates the associated objects in CloudFront')
    )

    help = 'Syncs the complete MEDIA_ROOT structure and files to S3 into the given bucket name.'
    args = 'bucket_name'

    can_import_settings = True

    def handle(self, *args, **options):
        if not HAS_BOTO:
            raise ImportError("The boto Python library is not installed.")

        # Check for AWS keys in settings
        if not hasattr(settings, 'AWS_ACCESS_KEY_ID') or not hasattr(settings, 'AWS_SECRET_ACCESS_KEY'):
            raise CommandError('Missing AWS keys from settings file.  Please supply both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.')
        else:
            self.AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
            self.AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY

        if not hasattr(settings, 'AWS_BUCKET_NAME'):
            raise CommandError('Missing bucket name from settings file. Please add the AWS_BUCKET_NAME to your settings file.')
        else:
            if not settings.AWS_BUCKET_NAME:
                raise CommandError('AWS_BUCKET_NAME cannot be empty.')
        self.AWS_BUCKET_NAME = settings.AWS_BUCKET_NAME

        if not hasattr(settings, 'MEDIA_ROOT'):
            raise CommandError('MEDIA_ROOT must be set in your settings.')
        else:
            if not settings.MEDIA_ROOT:
                raise CommandError('MEDIA_ROOT must be set in your settings.')

        self.AWS_CLOUDFRONT_DISTRIBUTION = getattr(settings, 'AWS_CLOUDFRONT_DISTRIBUTION', '')

        self.SYNC_S3_RENAME_GZIP_EXT = \
            getattr(settings, 'SYNC_S3_RENAME_GZIP_EXT', '.gz')

        self.verbosity = int(options.get('verbosity'))
        self.prefix = options.get('prefix')
        self.do_gzip = options.get('gzip')
        self.rename_gzip = options.get('renamegzip')
        self.do_expires = options.get('expires')
        self.do_force = options.get('force')
        self.invalidate = options.get('invalidate')
        self.DIRECTORY = options.get('dir')
        self.FILTER_LIST = getattr(settings, 'FILTER_LIST', self.FILTER_LIST)
        filter_list = options.get('filter_list')
        if filter_list:
            # command line option overrides default filter_list and
            # settings.filter_list
            self.FILTER_LIST = filter_list.split(',')

        # Now call the syncing method to walk the MEDIA_ROOT directory and
        # upload all files found.
        self.sync_s3()

        # Sending the invalidation request to CloudFront if the user
        # requested this action
        if self.invalidate:
            self.invalidate_objects_cf()

        print("")
        print("%d files uploaded." % self.upload_count)
        print("%d files skipped." % self.skip_count)

    def open_cf(self):
        """
        Returns an open connection to CloudFront
        """
        return boto.connect_cloudfront(
            self.AWS_ACCESS_KEY_ID, self.AWS_SECRET_ACCESS_KEY)

    def invalidate_objects_cf(self):
        """
        Split the invalidation request in groups of 1000 objects
        """
        if not self.AWS_CLOUDFRONT_DISTRIBUTION:
            raise CommandError(
                'An object invalidation was requested but the variable '
                'AWS_CLOUDFRONT_DISTRIBUTION is not present in your settings.')

        # We can't send more than 1000 objects in the same invalidation
        # request.
        chunk = 1000

        # Connecting to CloudFront
        conn = self.open_cf()

        # Splitting the object list
        objs = self.uploaded_files
        chunks = [objs[i:i + chunk] for i in range(0, len(objs), chunk)]

        # Invalidation requests
        for paths in chunks:
            conn.create_invalidation_request(
                self.AWS_CLOUDFRONT_DISTRIBUTION, paths)

    def sync_s3(self):
        """
        Walks the media directory and syncs files to S3
        """
        bucket, key = self.open_s3()
        os.path.walk(self.DIRECTORY, self.upload_s3, (bucket, key, self.AWS_BUCKET_NAME, self.DIRECTORY))

    def compress_string(self, s):
        """Gzip a given string."""
        zbuf = StringIO()
        zfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
        zfile.write(s)
        zfile.close()
        return zbuf.getvalue()

    def open_s3(self):
        """
        Opens connection to S3 returning bucket and key
        """
        conn = boto.connect_s3(self.AWS_ACCESS_KEY_ID, self.AWS_SECRET_ACCESS_KEY)
        try:
            bucket = conn.get_bucket(self.AWS_BUCKET_NAME)
        except boto.exception.S3ResponseError:
            bucket = conn.create_bucket(self.AWS_BUCKET_NAME)
        return bucket, boto.s3.key.Key(bucket)

    def upload_s3(self, arg, dirname, names):
        """
        This is the callback to os.path.walk and where much of the work happens
        """
        bucket, key, bucket_name, root_dir = arg

        # Skip directories we don't want to sync
        if os.path.basename(dirname) in self.FILTER_LIST:
            # prevent walk from processing subfiles/subdirs below the ignored one
            del names[:]
            return

        # Later we assume the MEDIA_ROOT ends with a trailing slash
        if not root_dir.endswith(os.path.sep):
            root_dir = root_dir + os.path.sep

        for file in names:
            headers = {}

            if file in self.FILTER_LIST:
                continue  # Skip files we don't want to sync

            filename = os.path.join(dirname, file)
            if os.path.isdir(filename):
                continue  # Don't try to upload directories

            file_key = filename[len(root_dir):]
            if self.prefix:
                file_key = '%s/%s' % (self.prefix, file_key)

            # Check if file on S3 is older than local file, if so, upload
            if not self.do_force:
                s3_key = bucket.get_key(file_key)
                if s3_key:
                    s3_datetime = datetime.datetime(*time.strptime(
                        s3_key.last_modified, '%a, %d %b %Y %H:%M:%S %Z')[0:6])
                    local_datetime = datetime.datetime.utcfromtimestamp(
                        os.stat(filename).st_mtime)
                    if local_datetime < s3_datetime:
                        self.skip_count += 1
                        if self.verbosity > 1:
                            print("File %s hasn't been modified since last being uploaded" % file_key)
                        continue

            # File is newer, let's process and upload
            if self.verbosity > 0:
                print("Uploading %s..." % file_key)

            content_type = mimetypes.guess_type(filename)[0]
            if content_type:
                headers['Content-Type'] = content_type
            file_obj = open(filename, 'rb')
            file_size = os.fstat(file_obj.fileno()).st_size
            filedata = file_obj.read()
            if self.do_gzip:
                # Gzipping only if file is large enough (>1K is recommended)
                # and only if file is a common text type (not a binary file)
                if file_size > 1024 and content_type in self.GZIP_CONTENT_TYPES:
                    filedata = self.compress_string(filedata)
                    if self.rename_gzip:
                        # If rename_gzip is True, then rename the file
                        # by appending an extension (like '.gz)' to
                        # original filename.
                        file_key = '%s.%s' % (
                            file_key, self.SYNC_S3_RENAME_GZIP_EXT)
                    headers['Content-Encoding'] = 'gzip'
                    if self.verbosity > 1:
                        print("\tgzipped: %dk to %dk" % (file_size / 1024, len(filedata) / 1024))
            if self.do_expires:
                # HTTP/1.0
                headers['Expires'] = '%s GMT' % (email.Utils.formatdate(time.mktime((datetime.datetime.now() + datetime.timedelta(days=365 * 2)).timetuple())))
                # HTTP/1.1
                headers['Cache-Control'] = 'max-age %d' % (3600 * 24 * 365 * 2)
                if self.verbosity > 1:
                    print("\texpires: %s" % headers['Expires'])
                    print("\tcache-control: %s" % headers['Cache-Control'])

            try:
                key.name = file_key
                key.set_contents_from_string(filedata, headers, replace=True)
                key.set_acl('public-read')
            except boto.exception.S3CreateError as e:
                print("Failed: %s" % e)
            except Exception as e:
                print(e)
                raise
            else:
                self.upload_count += 1
                self.uploaded_files.append(file_key)

            file_obj.close()
