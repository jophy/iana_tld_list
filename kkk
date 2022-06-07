# -*- coding:utf-8 -*-
__author__ = 'Jophy'
import requests
import os
import re


class IANA():
    def __init__(self):
        self.url = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"
        self.iana_url = "https://www.iana.org/domains/root/db/"

        self.dir = "data"
        self.tlds_filename = "tlds-alpha-by-domain.txt"
        self.tld_list_filename = "tldlist.txt"
        self.tld_json = "tld.json"

        if os.path.exists(self.dir + '/' + self.tld_list_filename):
            res = raw_input("File Found ! Still Continue Press Y or N.")
            if res.lower() == "y":
                self._init_File()
                self._get_TLD_File()
                self.get_TLD_Info()
                self.output_JSON()
            else:
                self.output_JSON()
                pass  # do some jobs
        else:
            self._init_File()
            self._get_TLD_File()
            self.get_TLD_Info()
            self.output_JSON()

    def _init_File(self):
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        with open(self.dir + '/' + self.tld_list_filename, "w") as f:
            f.close()

    def _get_TLD_File(self):
        r = requests.get(self.url).content
        with open(self.dir + '/' + self.tlds_filename, "w") as f:
            f.write(r)
            f.close()

    def _fetch_Server(self, tld):
        url = "{0}{1}.html".format(self.iana_url, tld)
        while 1:
            try:
                r = requests.get(url).content
            except:
                print tld + " Fetch Failed."
                continue
            else:
                return r

    def _parse(self, tld, content):
        output = {}
        if "Generic top-level domain" in content:
            output["type"] = "gTLD"
        elif "Infrastructure top-level domain" in content:
            output["type"] = "iTLD"
        elif "Sponsored top-level domain" in content:
            output["type"] = "gTLD"  # i.e  .asia
        else:
            output["type"] = "ccTLD"
        output["tld"] = tld
        dm = re.compile(r"<title>IANA — (.*) Domain Delegation Data</title>").findall(content)
        nic = re.compile(r'<b>URL for registration services:</b> <a href="(.*)">.*</a><br/>').findall(content)
        whois = re.compile(r'<b>WHOIS Server:</b>\s*(\S*)\s*</p>').findall(content)
        if len(dm) == 0:
            output["dm"] = "NULL"
        else:
            output["dm"] = dm[0].lower()
        if len(nic) == 0:
            output["nic"] = "NULL"
        else:
            output["nic"] = nic[0]
        if len(whois) == 0:
            output["whois"] = "NULL"
        else:
            output["whois"] = whois[0]
        if "xn--" in tld:
            output["isIDN"] = "True"
        else:
            output["isIDN"] = "False"
        output = "{0} -- {1} -- {2} -- {3} -- {4} -- {5}".format(output["tld"],
                                                                 output["dm"],
                                                                 output["isIDN"],
                                                                 output["type"],
                                                                 output["nic"],
                                                                 output["whois"])
        return output

    def get_TLD_Info(self):
        with open(self.dir + "/" + self.tlds_filename, "r") as f:
            tlds = f.readlines()
            del tlds[0]
            f.close()
        for i in tlds:
            tld = i.strip().lower()
            content = self._fetch_Server(tld)
            output = self._parse(tld, content)
            print output
            with open(self.dir + "/" + self.tld_list_filename, "a") as f:
                f.write(output + "\n")
                f.close()
            # break

    def output_JSON(self):
        output_dict = {}
        with open(self.dir + "/" + self.tld_list_filename, "r") as f:
            for i in f.readlines():
                dict = {}
                tld, dm, isIDN, type, nic, whois = i.strip().split(" -- ")
                dict["dm"] = dm
                dict["isIDN"] = isIDN
                dict["type"] = type
                dict["nic"] = nic
                dict["whois"] = whois
                output_dict[dm] = dict
            f.close()
        import json
        output_json = json.dumps(output_dict, sort_keys=True, indent=4, encoding="utf-8", ensure_ascii=False)
        with open(self.dir + "/" + self.tld_json, "w") as f:
            f.write(output_json)
            f.close()

if __name__ == '__main__':
    i = IANA()
