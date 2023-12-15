#!/usr/bin/env python

import itertools
import re
import sys

from splunklib.searchcommands import dispatch, EventingCommand, Configuration, Option, validators


@Configuration()
class CombinationsCommand(EventingCommand):
    """ Calculates permutations for an mv field """

    count = Option(
        require=False,
        default="2",
    )

    delim = Option(
        require=False,
        default=";"
    )

    outputfield = Option(
        require=False,
        default="result",
        validate=validators.Fieldname()
    )

    with_replacement = Option(
        require=False,
        default=False,
        validate=validators.Boolean()
    )

    def transform(self, records):
        if len(self.fieldnames) != 1:
            raise ValueError(f"Expected 1 fieldname, {len(self.fieldnames)} given")
        
        field = self.fieldnames[0]
        count_is_field = not bool(re.match(r"^\d+$", self.count))

        if self.with_replacement:
            func = itertools.combinations_with_replacement
        else:
            func = itertools.combinations

        for record in records:
            if field not in record:
                continue
            # elif not isinstance(record[field], list):
            #     continue

            if count_is_field and self.count not in record:
                continue
            elif count_is_field:
                try:
                    count = int(record[self.count])
                except ValueError:
                    raise
            else:
                count = int(self.count)

            record[self.outputfield] = []
            for pair in func(record[field], count):
                record[self.outputfield].append(self.delim.join(pair))
            yield record

dispatch(CombinationsCommand, sys.argv, sys.stdin, sys.stdout, __name__)
