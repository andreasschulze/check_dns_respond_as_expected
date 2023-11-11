#!/usr/bin/env python3

""" check dns respond as expected """

# Andreas Schulze, 2023, https://github.com/andreasschulze

import logging
import re
import os
import sys

import dns.resolver
import dns.zone

def check_nxdomain_or_nodata(qname, qtype, expected_exception):
    """
    check nxdomain or nodata response from DNS for *one* qname and qtype
    return 0 (OK) or 1 (NOT OK)
    """

    if expected_exception == dns.resolver.NXDOMAIN:
        rcode='NXDOMAIN'
    elif expected_exception == dns.resolver.NoAnswer:
        rcode='NODATA'
    else:
        logging.error('ERROR: program error, unexpected exception')
        sys.exit(1)

    try:
        answer = dns.resolver.resolve(qname, qtype)
    except expected_exception:
        logging.info('OK: %s/%s', qname, qtype)
        return 0
    except dns.resolver.NXDOMAIN:
        logging.error('ERROR: "%s" returned NXDOMAIN', qname)
        return 1

    # no exception mean: entry exist where it should not
    logging.error('ERROR: %s/%s returned data where %s is expected', qname, qtype, rcode)
    logging.debug('expected:\n%s\ngot:', rcode)
    for rdata in answer:
        logging.debug('%s', rdata)

    return 1

def check_expexted_data(filename):
    """
    check data in args.expected_data present in DNS
    return the number of found errors/unexpected data
    """

    errors = 0
    try:
        expected_rrsets = dns.zone.from_file(filename,
                                             '.',
                                             check_origin=False,
                                             relativize=False)
    except dns.exception.SyntaxError as exception:
        logging.error('ERROR: invalid data in %s', exception)
        return 1

    for qname, rdataset in expected_rrsets.iterate_rdatasets():
        qtype   = dns.rdatatype.to_text(rdataset.rdtype)
        answers = dns.resolver.resolve(qname, qtype)

        answer_rdataset = dns.rdataset.Rdataset(dns.rdataclass.IN, rdataset.rdtype)
        answer_rdataset.update_ttl(rdataset.ttl)
        for _rr in answers:
            answer_rdataset.add(_rr)

        if answer_rdataset == rdataset:
            logging.info('OK: %s/%s', qname, dns.rdatatype.to_text(rdataset.rdtype))
        else:
            errors += 1
            logging.error('ERROR: %s/%s returned unexpected data',
                          qname, dns.rdatatype.to_text(rdataset.rdtype))
            logging.debug('expected:\n%s\ngot:\n%s', rdataset, answer_rdataset)

    return errors

def check_absent_data(file, expected_exception):
    """
    check data in file (nxdomain or nodata) are not present in DNS
    return the number of found errors/unexpected data
    """

    errors = 0
    comment_line = re.compile('^#')
    empty_line = re.compile('^$')

    with open(file, 'r', encoding='utf-8') as _f:
        line_number = 0
        while True:
            line = _f.readline()
            line_number += 1
            if line == '':
                break

            # ignore comments and empty lines
            if comment_line.match(line):
                continue
            if empty_line.match(line):
                continue

            # remove the tailing linefeed
            line = line.rstrip()

            # check if there are really two fields present
            try:
                [qname, qtype] = line.split()
            except ValueError:
                errors += 1
                logging.error('ERROR: line %i: not exact 2 fields in "%s"', line_number, line)
                continue

            # verify the two fields
            assert qname != ''
            try:
                _qname = dns.name.from_text(qname, origin=None)
            except dns.name.EmptyLabel:
                errors += 1
                logging.error('ERROR: line %i: not a valid qname in "%s"', line_number, line)
                continue

            if not _qname.is_absolute():
                errors += 1
                logging.error('ERROR: line %i: no absolute label in "%s"', line_number, line)
                continue

            try:
                dns.rdatatype.from_text(qtype)
            except dns.rdatatype.UnknownRdatatype:
                errors += 1
                logging.error('ERROR: line %i: unknown qtype in "%s"', line_number, line)
                continue

            # a valid line was found
            # print(f'OK: line {line_number}: qname={qname}, qtype={qtype}')

            errors = errors + check_nxdomain_or_nodata(qname, qtype, expected_exception)

    return errors

# the main program ...
# takes no arguments, environment only
NUM_ERRORS         = 0
LOG_LEVEL          = logging.INFO
expected_data_file = os.getenv('EXPECTED_DATA_FILE', 'expected')
nodata_file        = os.getenv('NODATA_FILE', 'nodata')
nxdomain_file      = os.getenv('NXDOMAIN_FILE', 'nxdomain')

if os.getenv('VERBOSE'):
    LOG_LEVEL = logging.DEBUG
logging.basicConfig(format='%(message)s', level=LOG_LEVEL)

if os.path.exists(expected_data_file):
    logging.debug('checking expected data from "%s" ...', expected_data_file)
    NUM_ERRORS = NUM_ERRORS + check_expexted_data(expected_data_file)
else:
    logging.warning('WARNING: file "%s" not found, skip checking expected data ...',
                    expected_data_file)

if os.path.exists(nodata_file):
    logging.debug('checking nodata from "%s" ...', nodata_file)
    NUM_ERRORS = NUM_ERRORS + check_absent_data(nodata_file, dns.resolver.NoAnswer)
else:
    logging.warning('WARNING: file "%s" not found, skip checking nodata ...',
                    nodata_file)

if os.path.exists(nxdomain_file):
    logging.debug('checking nxdomain from "%s" ...', nxdomain_file)
    NUM_ERRORS = NUM_ERRORS + check_absent_data(nxdomain_file, dns.resolver.NXDOMAIN)
else:
    logging.warning('WARNING: file "%s" not found, skip checking nxdomain ...',
                    nxdomain_file)

logging.debug('%d problems', NUM_ERRORS)
sys.exit(NUM_ERRORS)
