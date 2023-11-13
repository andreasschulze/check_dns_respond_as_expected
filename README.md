# check_dns_respond_as_expected

[![markdownlint](https://github.com/andreasschulze/check_dns_respond_as_expected/actions/workflows/markdownlint.yml/badge.svg)](https://github.com/andreasschulze/check_dns_respond_as_expected/actions/workflows/markdownlint.yml)
[![pylint](https://github.com/andreasschulze/check_dns_respond_as_expected/actions/workflows/pylint.yml/badge.svg)](https://github.com/andreasschulze/check_dns_respond_as_expected/actions/workflows/pylint.yml)

Challenge: you plan to modify a DNS resolver. You want to be sure, nothing
will break. Define sample records with expected responses and let this script
check, every response from the DNS match the defined, expected value.
Now, change your DNS resolver. Then recheck, every query is still answered
with expected responses.

## Requirements

* python3
* dnspython

* a file containing the expected DNS data
* a file containing DNS label expected to be answered with NODATA
* a file containing DNS label expected to be answered with NXDOMAIN

## Environment

The script use the following environment variables:

* `EXPECTED_DATA_FILE`

  alternative filename for expected data

  Default if unset: `./expected`

* `NODATA_FILE`

  alternative filename for DNS label expected to be answered with NODATA

  Default if unset: `./nodata`

* `NXDOMAIN_FILE`

  alternative filename for DNS label expected to be answered with NXDOMAIN

  Default if unset: `./nxdomain`

* `VERBOSE`

  if set with any value (even `0` or `no`) the script produce more verbose
  output and a summary about the number of unexpected data found

  Default if unset: normal output

## Usage

Create a file with expected data. It's content is similar to a usual zone file
defined by [RFC 1035](https://datatracker.ietf.org/doc/html/rfc1035)

You **should** use fully qualified domain names. Every DNS label should contain
a domain part and end with a dot.

TTL values don't matter for comparison. They are completely ignored. But
dnspython require values are present. A convenient solution is to write
`$TTL 1h` as the first line.

```text
$TTL 1h
example.com.  A   93.184.216.34
example.com.  MX  0 .
```

The script can also check, values are **not** present in the DNS. These are to
be defined in two files `nodata` and `nxdomain`. This are simple text files with
strictly two columns. You **must** use fully qualified domain names. Every DNS
label must contain a domain part and end with a dot.

## Return code

The script's exit code is the number of unexpected data found.
