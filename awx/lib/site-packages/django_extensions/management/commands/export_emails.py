from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from optparse import make_option
from sys import stdout
from csv import writer

FORMATS = [
    'address',
    'emails',
    'google',
    'outlook',
    'linkedin',
    'vcard',
]


def full_name(first_name, last_name, username, **extra):
    name = u" ".join(n for n in [first_name, last_name] if n)
    if not name:
        return username
    return name


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--group', '-g', action='store', dest='group', default=None,
                    help='Limit to users which are part of the supplied group name'),
        make_option('--format', '-f', action='store', dest='format', default=FORMATS[0],
                    help="output format. May be one of '" + "', '".join(FORMATS) + "'."),
    )

    help = ("Export user email address list in one of a number of formats.")
    args = "[output file]"
    label = 'filename to save to'

    requires_model_validation = True
    can_import_settings = True
    encoding = 'utf-8'  # RED_FLAG: add as an option -DougN

    def handle(self, *args, **options):
        if len(args) > 1:
            raise CommandError("extra arguments supplied")
        group = options['group']
        if group and not Group.objects.filter(name=group).count() == 1:
            names = u"', '".join(g['name'] for g in Group.objects.values('name')).encode('utf-8')
            if names:
                names = "'" + names + "'."
            raise CommandError("Unknown group '" + group + "'. Valid group names are: " + names)
        if len(args) and args[0] != '-':
            outfile = open(args[0], 'w')
        else:
            outfile = stdout

        qs = User.objects.all().order_by('last_name', 'first_name', 'username', 'email')
        if group:
            qs = qs.filter(group__name=group).distinct()
        qs = qs.values('last_name', 'first_name', 'username', 'email')
        getattr(self, options['format'])(qs, outfile)

    def address(self, qs, out):
        """simple single entry per line in the format of:
            "full name" <my@address.com>;
        """
        out.write(u"\n".join(u'"%s" <%s>;' % (full_name(**ent), ent['email'])
                             for ent in qs).encode(self.encoding))
        out.write("\n")

    def emails(self, qs, out):
        """simpler single entry with email only in the format of:
            my@address.com,
        """
        out.write(u",\n".join(u'%s' % (ent['email']) for ent in qs).encode(self.encoding))
        out.write("\n")

    def google(self, qs, out):
        """CSV format suitable for importing into google GMail
        """
        csvf = writer(out)
        csvf.writerow(['Name', 'Email'])
        for ent in qs:
            csvf.writerow([full_name(**ent).encode(self.encoding),
                           ent['email'].encode(self.encoding)])

    def outlook(self, qs, out):
        """CSV format suitable for importing into outlook
        """
        csvf = writer(out)
        columns = ['Name', 'E-mail Address', 'Notes', 'E-mail 2 Address', 'E-mail 3 Address',
                   'Mobile Phone', 'Pager', 'Company', 'Job Title', 'Home Phone', 'Home Phone 2',
                   'Home Fax', 'Home Address', 'Business Phone', 'Business Phone 2',
                   'Business Fax', 'Business Address', 'Other Phone', 'Other Fax', 'Other Address']
        csvf.writerow(columns)
        empty = [''] * (len(columns) - 2)
        for ent in qs:
            csvf.writerow([full_name(**ent).encode(self.encoding),
                           ent['email'].encode(self.encoding)] + empty)

    def linkedin(self, qs, out):
        """CSV format suitable for importing into linkedin Groups.
        perfect for pre-approving members of a linkedin group.
        """
        csvf = writer(out)
        csvf.writerow(['First Name', 'Last Name', 'Email'])
        for ent in qs:
            csvf.writerow([ent['first_name'].encode(self.encoding),
                           ent['last_name'].encode(self.encoding),
                           ent['email'].encode(self.encoding)])

    def vcard(self, qs, out):
        try:
            import vobject
        except ImportError:
            print(self.style.ERROR("Please install python-vobject to use the vcard export format."))
            import sys
            sys.exit(1)
        for ent in qs:
            card = vobject.vCard()
            card.add('fn').value = full_name(**ent)
            if not ent['last_name'] and not ent['first_name']:
                # fallback to fullname, if both first and lastname are not declared
                card.add('n').value = vobject.vcard.Name(full_name(**ent))
            else:
                card.add('n').value = vobject.vcard.Name(ent['last_name'], ent['first_name'])
            emailpart = card.add('email')
            emailpart.value = ent['email']
            emailpart.type_param = 'INTERNET'
            out.write(card.serialize().encode(self.encoding))
