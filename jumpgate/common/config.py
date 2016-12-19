from ConfigParser import SafeConfigParser

PARSER = SafeConfigParser()


def configure(conf):
    PARSER.read(conf)
