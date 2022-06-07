#! /usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = "Jophy"
# updates and conversion to py3: mboot 2022-06-06

import requests
import os
import re
import sys
import json

from typing import Optional, Dict


class IANA:
    verbose: bool = False
    overwrite: bool = True
    interactive: bool = True
    downloadNew: bool = True

    tlds_filename: str = "tlds-alpha-by-domain.txt"
    url: str = f"https://data.iana.org/TLD/{tlds_filename}"

    iana_url: str = "https://www.iana.org/domains/root/db/"
    dir: str = "data"
    tld_list_filename: str = "tldlist.txt"
    tld_json: str = "tld.json"

    resultsPath: Optional[str] = None
    tldFilePath: Optional[str] = None
    resultsPathJson: Optional[str] = None

    output_dict: Dict = {}

    def _makePaths(self):
        psep = "/"

        self.resultsPath = self.dir + psep + self.tld_list_filename
        self.tldFilePath = self.dir + psep + self.tlds_filename
        self.resultsPathJson = self.dir + psep + self.tld_json

    def _decideDownLoadAndInteractive(self):
        self.downloadNew: bool = True

        if self.overwrite is False and self.interactive is True:
            self.downloadNew: bool = False

            if os.path.exists(self.resultsPath):
                msg = f"File {self.resultsPath} already exists; Do you want to overwrite? Y/[N]."
                res = input(msg)
                if res.lower() == "y":
                    self.downloadNew = True
            else:
                self.downloadNew = True

    def __init__(
        self,
        dirName: str = "data",
        verbose: bool = False,
        overwrite: bool = False,
        interactive: bool = True,
    ):
        self.verbose = verbose
        self.overwrite = overwrite
        self.interactive = interactive

        self.dir = dirName
        self._makePaths()

        self._decideDownLoadAndInteractive()

        if self.downloadNew:
            self._initResultsFile()
            self._getTldFile()
            self._getTldInfo()

        self._outputJSON()

    def _initResultsFile(self):
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

        with open(self.resultsPath, "w", encoding="utf8") as f:
            f.close()

    def _getTldFile(self):
        r = requests.get(self.url)
        with open(self.tldFilePath, "w", encoding="utf8") as f:
            f.write(r.text)
            f.close()

    def _fetch_Server(self, tld):
        url = f"{self.iana_url}{tld}.html"

        n = 0
        while 1:
            n += 1
            try:
                r = requests.get(url)
                return r.text
            except Exception as e:
                print(f"{tld} Fetch Failed: {e}", file=sys.stderr)
                if n > 10:
                    msg = f"getting data url: {url} has retried {n} times without success"
                    print(msg, file=sys.stderr)
                    exit(101)

    def _parse(self, tld, content):
        output = {}

        # --------------------------------------
        if "Generic top-level domain" in content:
            output["type"] = "gTLD"
        elif "Infrastructure top-level domain" in content:
            output["type"] = "iTLD"
        elif "Sponsored top-level domain" in content:
            output["type"] = "gTLD"  # i.e  .asia
        else:
            output["type"] = "ccTLD"

        # --------------------------------------
        output["tld"] = tld

        # extract regex patterns with postprocessing
        zz = {
            "dm": {
                # NOTE THIS CAN BE UTF8
                "reg": r"<title>(.*) Domain Delegation Data</title>",
                "func": lambda x: x[0],
            },
            "nic": {
                "reg": r'<b>URL for registration services:</b> <a href="[^"]+">(.*)</a><br/>',
                "func": lambda x: x[0],
            },
            "whois": {
                "reg": r"<b>WHOIS Server:</b>\s*([\w.-]+)\s*",
                "func": lambda x: x[0].rstrip().lower(),
            },
            "lastUpdate": {
                "reg": r"Record last updated\s+(\d{4}-\d{2}-\d{2})",
                "func": lambda x: x[0].lower(),
            },
            "registration": {
                "reg": r"Registration date\s+(\d{4}-\d{2}-\d{2})",
                "func": lambda x: x[0].lower(),
            },
        }

        for k in zz:
            s = zz[k]["reg"]
            f = zz[k]["func"]
            xx = re.compile(s).findall(content)
            output[k] = str("NULL")
            if len(xx):
                output[k] = f(xx)

        # --------------------------------------
        output["isIDN"] = "False"
        if tld.startswith("xn--"):
            output["isIDN"] = "True"

        # --------------------------------------
        return " -- ".join(
            [
                output["tld"],
                output["dm"],  # utf-8
                output["isIDN"],
                output["type"],
                output["nic"],
                output["whois"],
                output["lastUpdate"],
                output["registration"],
            ],
        )

    def _doOneTld(self, tld: str):
        content = self._fetch_Server(tld)
        output = self._parse(tld, content)

        if self.verbose:
            print(output, file=sys.stderr)

        with open(self.resultsPath, "a", encoding="utf8") as f:
            f.write(output + "\n")
            f.close()

    def _getAllTlds(self):
        with open(self.tldFilePath, "r", encoding="utf8") as f:
            tlds = f.readlines()
            del tlds[0]
            f.close()
        return sorted(tlds)

    def _getTldInfo(self):
        tlds = self._getAllTlds()
        for i in tlds:
            tld = i.rstrip().lower()
            self._doOneTld(tld)

    def _fPathReadToDict(self):
        self.output_dict: Dict = {}

        with open(self.resultsPath, "r", encoding="utf8") as f:
            for i in f.readlines():
                xDict = {}

                (
                    xDict["tld"],
                    xDict["dm"],
                    xDict["isIDN"],
                    xDict["type"],
                    xDict["nic"],
                    xDict["whois"],
                    xDict["lastUpdate"],
                    xDict["registration"],
                ) = i.strip().split(" -- ")

                self.output_dict[xDict["dm"]] = xDict
            f.close()

    def _saveDictToJson(self):
        if self.output_dict.get("NULL"):
            del self.output_dict["NULL"]

        output_json = json.dumps(
            self.output_dict,
            indent=2,
            ensure_ascii=False,
        )

        with open(self.resultsPathJson, "w", encoding="utf8") as f:
            f.write(output_json)
            f.close()

    def _outputJSON(self):
        self._fPathReadToDict()
        self._saveDictToJson()

    def getInfoOnTld(self, tld: str):
        tld = tld.lower()
        if not tld.startswith("."):
            tld = "." + tld

        if tld not in self.output_dict:
            return None

        return self.output_dict[tld]


if __name__ == "__main__":
    i = IANA(
        verbose=True,
        overwrite=True,
        interactive=False,
    )
