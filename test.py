#! /usr/bin/env python3

from iana import IANA

# allow verbose messages during testing (all on stderr)
verbose = False

# by default the all tld file will be refreshed ever 24 hours,
# but you can force a new download anytime also
forceDownloadTld = False

# do you want to overwrite the results file ?
overwrite = True

# do you want interactive questions if files will be re-written?
interactive = False

# if autoProcessAll is True: all tld's will be processed (initial run > 20 minutes)
autoProcessAll = False

with_test_original = False

dirName = "/tmp/iana_data"

i = IANA(
    dirName=dirName,
    verbose=verbose,
    overwrite=overwrite,
    interactive=interactive,
    autoProcessAll=autoProcessAll,
    forceDownloadTld=forceDownloadTld,
)

print(i.getAllTlds())

tlds = [
    "nl",
    ".nl",
    "xxx",
    "not-exist",
]

for tld in tlds:
    data, status = i.getInfoOnOneTld(tld)
    print(tld, data, status)

if with_test_original:
    # test the original defaut behaviour
    i = IANA()
