#!/usr/bin/env python3

import csv
import sys


inf = csv.DictReader(sys.stdin)
outf = csv.DictWriter(sys.stdout, fieldnames=inf.fieldnames)
outf.writeheader()

for row in inf:
    if row["char"] and row["hex"]:
        pass
    elif row["char"]:
        row["hex"] = hex(ord(row["char"]))[2:]
    elif row["hex"]:
        row["char"] = chr(f"0x{row['hex']}")
    else:
        pass

    # raise ValueError(row)
    outf.writerow(row)