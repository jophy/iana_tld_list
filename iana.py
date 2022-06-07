#! /usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = "Jophy"
# updates and conversion to py3: mboot 2022-06-06

import requests
import os
import re
import sys
import json
import time
from typing import Optional, Dict, List


class IanaItem:
    tld: Optional[str] = None
    dm: Optional[str] = None
    isIDN: Optional[str] = None
    tldType: Optional[str] = None
    nic: Optional[str] = None
    whois: Optional[str] = None
    lastUpdate: Optional[str] = None
    registration: Optional[str] = None


class IANA:
    # all bool flags are default for the original behaviour of the IANA class
    verbose: bool = False
    overwrite: bool = True
    interactive: bool = True
    downloadNew: bool = True
    forceDownloadTld: bool = False

    # allow getting one tld at a time
    # if we do not process all tlds (20 minutes delay on initial run)
    #   we can fetch individual tld's one by one
    autoProcessAll: bool = True

    tlds_filename: str = "tlds-alpha-by-domain.txt"
    url: str = f"https://data.iana.org/TLD/{tlds_filename}"

    iana_url: str = "https://www.iana.org/domains/root/db/"
    xDir: str = "data"
    tld_list_filename: str = "tldlist.txt"
    tld_json: str = "tld.json"

    resultsPath: Optional[str] = None
    tldFilePath: Optional[str] = None
    resultsPathJson: Optional[str] = None

    allTlds: List = []
    outputDict: Dict = {}
    timeEpoch: int = 0

    # 24 hours in seconds
    reloadTldFileTimeInSeconds = 24 * 60 * 60

    def _makePaths(self):
        psep = "/"

        self.resultsPath = self.xDir + psep + self.tld_list_filename
        self.tldFilePath = self.xDir + psep + self.tlds_filename
        self.resultsPathJson = self.xDir + psep + self.tld_json

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

    def _autoProcessAllTlds(self):
        self._decideDownLoadAndInteractive()

        if self.downloadNew:
            self._getTldInfoAllTlds()

        self._saveAllTldsAsJsonToFile()

    def _getAllTldsAsArray(self):
        tlds: List = []
        with open(self.tldFilePath, "r") as f:
            for line in f.readlines():
                line = line.rstrip()

                if self.verbose:
                    print(line, file=sys.stderr)

                if not line.startswith("#"):
                    tld = line.lower()
                    tlds.append(tld)

        self.allTlds = sorted(tlds)

    def _getTldFile(self):
        if self.verbose:
            print(self.url, file=sys.stderr)

        # if the file is less then 24 hours old do not refresh unless force is active
        tt = int(os.path.getmtime(self.tldFilePath))
        tDiff = int(self.timeEpoch - tt)
        if self.forceDownloadTld is True or tDiff > self.reloadTldFileTimeInSeconds:
            if self.verbose:
                print(
                    f"file {self.tldFilePath} older then {tDiff} seconds, or forceDownloadTld = True: downloading fresh copy",
                    self.tldFilePath,
                    file=sys.stderr,
                )

            r = requests.get(self.url)
            with open(self.tldFilePath, "w", encoding="utf8") as f:
                f.write(r.text)

                if self.verbose:
                    print(r.text, file=sys.stderr)

        self._getAllTldsAsArray()

    def __init__(
        self,
        dirName: str = "data",
        verbose: bool = False,
        overwrite: bool = False,
        interactive: bool = True,
        autoProcessAll: bool = True,
        forceDownloadTld: bool = False,
    ):
        self.verbose = verbose
        self.overwrite = overwrite
        self.interactive = interactive
        self.autoProcessAll = autoProcessAll
        self.forceDownloadTld = forceDownloadTld

        self.timeEpoch = int(time.time())
        if self.verbose:
            print(f"time epoch: {self.timeEpoch}", file=sys.stderr)

        self.xDir = dirName
        if not os.path.exists(self.xDir):
            os.mkdir(self.xDir)
        self._makePaths()

        self._getTldFile()  # always refresh the tld all file from IANA

        # optionally process all tld's automatically or fetch them individually on demand later
        if self.autoProcessAll:
            self._autoProcessAllTlds()

    def _fetchOneTldFromIanaWeb(self, tld):
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

    def _parseDataForOneTld(self, tld, content):
        output = {}

        # --------------------------------------
        k = "tldType"
        if "Generic top-level domain" in content:
            output[k] = "gTLD"
        elif "Infrastructure top-level domain" in content:
            output[k] = "iTLD"
        elif "Sponsored top-level domain" in content:
            output[k] = "gTLD"  # i.e  .asia
        else:
            output[k] = "ccTLD"

        # --------------------------------------
        output["tld"] = tld  # this is the non utf-8 tld name

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
        k = "isIDN"
        output[k] = "False"
        if tld.startswith("xn--"):
            output[k] = "True"

        if self.verbose:
            print(output, file=sys.stderr)

        # --------------------------------------
        return output

    def _appendOneTldToREsultsFile(self, data):
        with open(self.resultsPath, "a", encoding="utf8") as f:
            f.write(data + "\n")

    def _convertDataToSplitableString(self, output: Dict) -> str:
        string = " -- ".join(
            [
                output["tld"],
                output["dm"],  # utf-8
                output["isIDN"],
                output["tldType"],
                output["nic"],
                output["whois"],
                output["lastUpdate"],
                output["registration"],
            ],
        )
        return string

    def fetchOneTldFromIana(self, tld):
        content = self._fetchOneTldFromIanaWeb(tld)
        output = self._parseDataForOneTld(tld, content)
        return output

    def _doOneTld(self, tld: str):
        output = self.getchOneTldFromIana(tld)
        string = self._convertDataToSplitableString(output)
        self._appendOneTldToREsultsFile(string)

    def _initResultsFile(self):
        with open(self.resultsPath, "w", encoding="utf8") as f:
            f.close()

    def _getTldInfoAllTlds(self):
        self._initResultsFile()
        for tld in self.allTlds:
            self._doOneTld(tld)

    def _readResultsPathAndConvertAllToDict(self):
        self.outputDict: Dict = {}

        with open(self.resultsPath, "r", encoding="utf8") as f:
            for i in f.readlines():
                xDict = {}

                (
                    xDict["tld"],
                    xDict["dm"],
                    xDict["isIDN"],
                    xDict["tldType"],
                    xDict["nic"],
                    xDict["whois"],
                    xDict["lastUpdate"],
                    xDict["registration"],
                ) = i.strip().split(" -- ")

                self.outputDict[xDict["dm"]] = xDict

    def _saveDictToJsonFile(self):
        if self.outputDict.get("NULL"):
            del self.outputDict["NULL"]

        output_json = json.dumps(
            self.outputDict,
            indent=2,
            ensure_ascii=False,
        )

        with open(self.resultsPathJson, "w", encoding="utf8") as f:
            f.write(output_json)

    def _saveAllTldsAsJsonToFile(self):
        self._readResultsPathAndConvertAllToDict()
        self._saveDictToJsonFile()

    def getInfoOnOneTld(self, tld: str):
        tld = tld.lower()

        if tld.startswith("."):
            tld = tld.lstrip(".")

        if tld not in self.allTlds:
            return None, "tldNotFound"

        if tld not in self.outputDict:
            data = self.fetchOneTldFromIana(tld)
            self.outputDict[tld] = data

        return self.outputDict[tld], None


if __name__ == "__main__":

    verbose = False
    verbose = True

    forceDownloadTld = True

    dirName = "/tmp/iana_data"

    i = IANA(
        dirName=dirName,
        verbose=verbose,
        overwrite=True,
        interactive=False,
        autoProcessAll=False,
        forceDownloadTld=forceDownloadTld,
    )

    if verbose:
        print(i.allTlds)

    tlds = [
        "nl",
        ".nl",
    ]

    for tld in tlds:
        data, status = i.getInfoOnOneTld(tld)
        print(tld, data, status)
