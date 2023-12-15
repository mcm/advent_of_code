#!/usr/bin/env python

import fnmatch
import sys
from collections import defaultdict
from string import Formatter

from splunklib.searchcommands import dispatch, StreamingCommand, Configuration, Option, validators


@Configuration()
class ExpandTokensCommand(StreamingCommand):
    """ Evaluates tokens in a field """

    default = Option(
        require=False,
        default=None,
        # validate=validators.Fieldname()
    )

    def stream(self, records):
        self.logger.debug("ExpandTokensCommand: %s", self)

        # if len(self.fieldnames) != 1:
        #     raise ValueError(f"Expected 1 fieldname, {len(self.fieldnames)} given")

        for record in records:
            if self.default:
                record = defaultdict(lambda: self.default, **record)

            for field in self.fieldnames:
                record[field] = Formatter().vformat(record[field], (), record)

            yield record

dispatch(ExpandTokensCommand, sys.argv, sys.stdin, sys.stdout, __name__)
