#!/usr/bin/env python3

import csv
import datetime
import glob
import os
import re
import sys

from splunklib import modularinput as mi


APP_DIR = os.path.join(os.environ["SPLUNK_HOME"], "etc", "apps", "advent_of_code")
DEFAULT_DATA_DIR = os.path.join(APP_DIR, "default", "data", "advent_of_code")
LOCAL_DATA_DIR = os.path.join(APP_DIR, "local", "data", "advent_of_code")
LOOKUP_DIR = os.path.join(APP_DIR, "lookups")


today = datetime.date.today()


class AdventOfCodeDatagenScript(mi.Script):
    _conf = None

    def get_scheme(self):
        scheme = mi.Scheme("Advent of Code Datagen")
        scheme.description = "Generate lookups from Advent of Code data"
        scheme.use_external_validation = False
        scheme.use_single_instance = False
        return scheme
    
    def is_lookupgen_enabled(self, year):
        try:
            disabled = self.service.confs["advent_of_code"][f"lookupgen-{year}"]["disabled"]
        except KeyError:
            return False
        return disabled.lower() in ("0", "false", "no")
    
    def generate_lookup(self, year, srcfile, destfile):
        m = re.match(r"^(\d+)_.+\.txt$", os.path.basename(srcfile))
        day = m.groups()[0]
        try:
            header = self.service.confs["advent_of_code"][f"lookupgen-{year}"][f"headers.{day}"]
        except (AttributeError, KeyError):
            return

        with open(destfile, "w") as outf:
            csvf = csv.DictWriter(outf, fieldnames=[header])
            csvf.writeheader()
            with open(srcfile, "r") as inf:
                for line in inf:
                    csvf.writerow({header: line.strip()})

    def generate_lookups(self, lookuptype):
        if today.month == 12:
            max_year = today.year + 1
        else:
            max_year = today.year

        for aoc_year in range(2015, max_year):
            if not self.is_lookupgen_enabled(aoc_year):
                # sys.stderr.write(f"Not generating lookups for {aoc_year}: disabled\n")
                continue

            for day in range(1, 26):
                lookups = []
                for data_dir in (LOCAL_DATA_DIR, DEFAULT_DATA_DIR):
                    data_dir = os.path.join(data_dir, str(aoc_year), lookuptype)
                    if not os.path.exists(data_dir):
                        # sys.stderr.write(f"Skipping {data_dir} which doesn't exist\n")
                        continue
                    path = os.path.join(data_dir, f"{day:02}_*.txt")
                    # sys.stderr.write(f"Looking for files: {path}\n")
                    for srcfile in glob.glob(path):
                        # sys.stderr.write(f"Trying to make a lookup from {srcfile}\n")
                        filename, _ = os.path.splitext(os.path.basename(srcfile))
                        if filename in lookups:
                            continue
                        destfile = os.path.join(LOOKUP_DIR, f"{aoc_year}-{filename}.csv")
                        self.generate_lookup(aoc_year, srcfile, destfile)
                        lookups.append(filename)
        # for aoc_year in os.listdir(DATA_DIR):
        #     if not self.is_lookupgen_enabled(aoc_year):
        #         continue
        #     path = os.path.join(DATA_DIR, aoc_year, lookuptype)
        #     for srcfile in os.listdir(path):
        #         m = re.match(r"^(\d+_.+)\.txt$", srcfile)
        #         if not m:
        #             continue
        #         destfile = os.path.join(LOOKUP_DIR, f"{aoc_year}-{m.groups()[0]}.csv")
        #         self.generate_lookup(aoc_year, os.path.join(path, srcfile), destfile)
                
    def stream_events(self, inputs, ew):
        try:
            os.makedirs(LOOKUP_DIR)
        except:
            pass

        for input_name in inputs.inputs:
            path = input_name.split("://")[1]
            try:
                self.generate_lookups(path)
            except:
                import traceback
                sys.stderr.write(traceback.format_exc())
                raise


if __name__ == "__main__":
    sys.exit(AdventOfCodeDatagenScript().run(sys.argv))
    # AdventOfCodeDatagenScript().generate_lookups("examples")