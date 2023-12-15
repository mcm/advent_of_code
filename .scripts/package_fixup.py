#!/usr/bin/env python3

import argparse
import gzip
import os
import shutil
import tarfile
import tempfile


ap = argparse.ArgumentParser()
ap.add_argument("file")
args = ap.parse_args()


if not os.path.isfile(args.file):
    print(f"{args.file} is not a file")
    exit()

with open(args.file, "rb") as f:
    magic = f.read(2)

if magic != b"\x1f\x8b":
    print("Not a gzip file")
    exit()


with gzip.GzipFile(args.file, "rb") as fo1:
    with tarfile.TarFile(fileobj=fo1) as tf1:
        with tempfile.NamedTemporaryFile(delete=False) as outfile:
            with gzip.GzipFile(fileobj=outfile.file, mode="w") as fo2:
                with tarfile.TarFile(fileobj=fo2, mode="w", format=tarfile.USTAR_FORMAT) as tf2:
                    app_dir = None

                    for m in tf1.getmembers():
                        ###
                        # Remove PAX headers for older/non-POSIX tar implementations
                        ###
                        if m.pax_headers:
                            m.pax_headers = {}

                        ###
                        # Remove ._ files created on macOS
                        ###
                        if m.name.startswith("._") or os.path.basename(m.name).startswith("._"):
                            continue

                        # Figure out what the app directory is based on the first entry in the tarball
                        if app_dir is None:
                            if "/" in m.name:
                                app_dir, _ = m.name.split("/", 1)
                            else:
                                app_dir = m.name

                        ###
                        # Bail if there's a local directory, or a local.meta file
                        ###
                        if m.name.startswith(f"{app_dir}/local") or m.name == f"{app_dir}/meta/local.meta":
                            print(f"ERROR: local path ({m.name}) found. Unable to correct this.")
                            exit()

                        ###
                        # Force the uid/gid to 0 instead of whatever was given to us
                        ###
                        m.uid = m.gid = 0

                        ###
                        # Normalize permissions
                        ###
                        if m.type == tarfile.DIRTYPE or (m.name.startswith(f"{app_dir}/bin") and not m.name.endswith("/README")):
                            if m.mode != 0o755:
                                m.mode = 0o755
                        else:
                            if m.mode != 0o644:
                                m.mode = 0o644

                        mf = tf1.extractfile(m)
                        tf2.addfile(m, mf)

        shutil.move(outfile.name, args.file)