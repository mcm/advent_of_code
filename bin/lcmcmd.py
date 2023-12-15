#!/usr/bin/env python

import fnmatch
import functools
import math
import sys

from splunklib.searchcommands import dispatch, StreamingCommand, Configuration, Option, validators


def lcm(a, b):
    return abs(a * b) // math.gcd(a, b)


@Configuration()
class LCMCommand(StreamingCommand):
    """ Finds the lowest common denominator """

    outputfield = Option(
        require=False,
        default="result",
        validate=validators.Fieldname()
    )

    def stream(self, records):
        if len(self.fieldnames) == 0:
            raise ValueError(f"Expected 1 or more field names, {len(self.fieldnames)} given")

        for record in records:
            values = []

            fieldnames = []
            for fieldname in self.fieldnames:
                if "*" not in fieldname:
                    fieldnames.append(fieldname)
                    continue

                for field in record:
                    if fnmatch.fnmatch(field, fieldname):
                        fieldnames.append(field)

            for fieldname in fieldnames:
                value = record[fieldname]
                if not isinstance(value, list):
                    value = [value]

                for item in value:
                    try:
                        values.append(int(item))
                    except ValueError:
                        continue
                    
            if len(values) == 0:
                record[self.outputfield] = None
            elif len(values) == 1:
                record[self.outputfield] = values[0]
            else:
                record[self.outputfield] = functools.reduce(lcm, values)

            yield record

dispatch(LCMCommand, sys.argv, sys.stdin, sys.stdout, __name__)
