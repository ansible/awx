"""
COMMAND-LINE SPECIFIC STUFF
=============================================================================

"""

import markdown
import sys
import optparse
import codecs
try: 
    import yaml
except ImportError: #pragma: no cover
    import json as yaml

import logging
from logging import DEBUG, INFO, CRITICAL

logger =  logging.getLogger('MARKDOWN')

def parse_options(args=None, values=None):
    """
    Define and parse `optparse` options for command-line usage.
    """
    usage = """%prog [options] [INPUTFILE]
       (STDIN is assumed if no INPUTFILE is given)"""
    desc = "A Python implementation of John Gruber's Markdown. " \
           "https://pythonhosted.org/Markdown/"
    ver = "%%prog %s" % markdown.version
    
    parser = optparse.OptionParser(usage=usage, description=desc, version=ver)
    parser.add_option("-f", "--file", dest="filename", default=None,
                      help="Write output to OUTPUT_FILE. Defaults to STDOUT.",
                      metavar="OUTPUT_FILE")
    parser.add_option("-e", "--encoding", dest="encoding",
                      help="Encoding for input and output files.",)
    parser.add_option("-s", "--safe", dest="safe", default=False,
                      metavar="SAFE_MODE",
                      help="Deprecated! 'replace', 'remove' or 'escape' HTML tags in input")
    parser.add_option("-o", "--output_format", dest="output_format", 
                      default='xhtml1', metavar="OUTPUT_FORMAT",
                      help="'xhtml1' (default), 'html4' or 'html5'.")
    parser.add_option("-n", "--no_lazy_ol", dest="lazy_ol", 
                      action='store_false', default=True,
                      help="Observe number of first item of ordered lists.")
    parser.add_option("-x", "--extension", action="append", dest="extensions",
                      help = "Load extension EXTENSION.", metavar="EXTENSION")
    parser.add_option("-c", "--extension_configs", dest="configfile", default=None,
                      help="Read extension configurations from CONFIG_FILE. "
                      "CONFIG_FILE must be of JSON or YAML format. YAML format requires "
                      "that a python YAML library be installed. The parsed JSON or YAML "
                      "must result in a python dictionary which would be accepted by the "
                      "'extension_configs' keyword on the markdown.Markdown class. "
                      "The extensions must also be loaded with the `--extension` option.",
                      metavar="CONFIG_FILE")
    parser.add_option("-q", "--quiet", default = CRITICAL,
                      action="store_const", const=CRITICAL+10, dest="verbose",
                      help="Suppress all warnings.")
    parser.add_option("-v", "--verbose",
                      action="store_const", const=INFO, dest="verbose",
                      help="Print all warnings.")
    parser.add_option("--noisy",
                      action="store_const", const=DEBUG, dest="verbose",
                      help="Print debug messages.")

    (options, args) = parser.parse_args(args, values)

    if len(args) == 0:
        input_file = None
    else:
        input_file = args[0]

    if not options.extensions:
        options.extensions = []

    extension_configs = {}
    if options.configfile:
        with codecs.open(options.configfile, mode="r", encoding=options.encoding) as fp:
            try:
                extension_configs = yaml.load(fp)
            except Exception as e:
                message = "Failed parsing extension config file: %s" % options.configfile
                e.args = (message,) + e.args[1:]
                raise

    return {'input': input_file,
            'output': options.filename,
            'safe_mode': options.safe,
            'extensions': options.extensions,
            'extension_configs': extension_configs,
            'encoding': options.encoding,
            'output_format': options.output_format,
            'lazy_ol': options.lazy_ol}, options.verbose

def run(): #pragma: no cover
    """Run Markdown from the command line."""

    # Parse options and adjust logging level if necessary
    options, logging_level = parse_options()
    if not options: sys.exit(2)
    logger.setLevel(logging_level)
    logger.addHandler(logging.StreamHandler())

    # Run
    markdown.markdownFromFile(**options)

if __name__ == '__main__': #pragma: no cover
    # Support running module as a commandline command. 
    # Python 2.5 & 2.6 do: `python -m markdown.__main__ [options] [args]`.
    # Python 2.7 & 3.x do: `python -m markdown [options] [args]`.
    run()
