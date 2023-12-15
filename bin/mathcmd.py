#!/usr/bin/env python

import sys

from simpleeval import simple_eval
from splunklib.searchcommands import dispatch, StreamingCommand, Configuration, Option, validators


@Configuration()
class MathCommand(StreamingCommand):
    """ Evaluates simple math in a field """

    outputfield = Option(
        require=False,
        default="result",
        validate=validators.Fieldname()
    )

    def stream(self, records):
        self.logger.debug("SemverCmpCommand: %s", self)

        if len(self.fieldnames) != 1:
            raise ValueError(f"Expected 1 fieldname, {len(self.fieldnames)} given")

        field = self.fieldnames[0]

        for record in records:
            if field not in record:
                continue

            names = {}
            for key in record:
                try:
                    names[key] = int(record[key])
                except ValueError:
                    continue

            try:
                record[self.outputfield] = simple_eval(record[field], names=names)
            except ValueError:
                continue

            yield record

dispatch(MathCommand, sys.argv, sys.stdin, sys.stdout, __name__)
