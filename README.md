# iana_tld_list

original author:
    "Jophy: https://github.com/jophy"

python 3 modifications and addidional behaviour:
    "mboot: https://github.com/maarten-boot"

A python script for fetching IANA Tldlist and parsing NIC website & Whois server.

### Usage: ###
>run python iana.py.
or see the test.py

1. Script will download the IANA database from https://data.iana.org/TLD/tlds-alpha-by-domain.txt.
    The file will be refreshed every 24 hours by default
2. It will fetch tld info one by one from https://www.iana.org/domains/root/db/ and create a tldlist.txt file finally.
3. At last, it will parse the tldlist.txt and create tld.json.

### Tips: ###
The default behaviour is:
- Script will check if there is a tldlist.txt file at the beginning of downloading the Database.
- You can press Y to override existing files.
- It will take you at least 20 minutes to process all the existing tld's from IANA. (Test on a DigitalOcean VPS)

### New Options ###
new options now allow better fine-tuning:
- no interactive behaviour
- always overwrite existing files
- caching the initial tld file
- fetching individual tld's with caching (no need for the initial download if you want to lookup only a few tld's)
- specify your own download path
- additional verbosity during testing

### License: ###
MIT License
