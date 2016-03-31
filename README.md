# iana_tld_list

A python script for fetching IANA Tldlist and parsing NIC website & Whois server.

### Usage: ###
>run python iana.py.

1. Script will download the IANA database from https://data.iana.org/TLD/tlds-alpha-by-domain.txt .
2. It will fetch tld info one by one from https://www.iana.org/domains/root/db/ and create a tldlist.txt file finally.
3. At last, it will parse the tldlist.txt and create tld.json.

### Tips: ###
Script will check if there is a tldlist.txt file at the beginning of downloading the Database.

You can press Y to override existing files.

### License: ###
MIT License