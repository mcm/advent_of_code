#!/usr/bin/env python

import csv
import os
import sys

from splunklib.searchcommands import dispatch, EventingCommand, Configuration, Option, validators


class LookupRange:
    def __init__(self, range_, result):
        self.range_min, self.range_max = map(int, range_.split("-"))
        if "-" in result:
            self.result_is_range = True
            self.result_min, self.result_max = map(int, result.split("-"))
        else:
            self.result_is_range = False
            self.result_min = self.result_max = int(result)

    def __str__(self):
        return f"{self.range_min}-{self.range_max} -> {self.result_min}-{self.result_max}"

    def __contains__(self, other):
        return self.range_min <= int(other) <= self.range_max
    
    def __getitem__(self, other):
        if other not in self:
            raise KeyError(other)
        if not self.result_is_range:
            return self.result_min
        result = (int(other) - self.range_min) + self.result_min
        # if other == "14":
        #     raise ValueError(f"{other} -> {result} ({int(other) - self.range_min}): {self.range_min} -> {self.range_max} :: {self.result_min} -> {self.result_max}")
        return result
    
    def get_chunk(self, other):
        if other not in self:
            raise KeyError(other)
        other = int(other)
        result_start = self.result_min + (other - self.range_min)
        result_end = self.result_max
        chunk_end = self.range_max
        return (chunk_end, result_start, result_end)
    

class RangeManager:
    def __init__(self):
        self.ranges = []

    def add_range(self, range_, result):
        self.ranges.append(LookupRange(range_, result))

    def find_next_range(self, other, range_end):
        other = int(other)
        ranges = [r for r in self.ranges if other < r.range_min and r.range_min <= range_end ]
        return ranges[0] if ranges else None
    
    def get_range(self, other):
        other = int(other)
        for r in self.ranges:
            if other in r:
                return r
        return None

    def __contains__(self, other):
        return self.get_range(other) is not None
    
    def __iter__(self):
        return iter(self.ranges)


@Configuration()
class RangeLookupCommand(EventingCommand):
    """ Performs a lookup against a table with ranges """

    lookup = Option(require=True)
    field = Option(require=True)
    field_in_lookup = Option(require=False)
    output_field = Option(require=True)
    output_field_in_lookup = Option(require=False)
    overwrite = Option(require=False, default=False)

    def transform(self, records):
        app_dir = os.path.join(os.environ["SPLUNK_HOME"], "etc", "apps", self.metadata.searchinfo.app)
        lookups_dir = os.path.join(app_dir, "lookups")
        lookup_path = os.path.join(lookups_dir, self.lookup)

        if not os.path.exists(lookup_path):
            raise ValueError(f"Unable to find lookup {lookup_path}")
        
        self.field_in_lookup = self.field_in_lookup or self.field
        self.output_field_in_lookup = self.output_field_in_lookup or self.output_field
        
        ranges = RangeManager()
        with open(lookup_path, "r") as f:
            csvf = csv.DictReader(f)
            for row in csvf:
                assert self.field_in_lookup in row
                assert self.output_field_in_lookup in row

                # data.append(LookupRange(row[self.field_in_lookup], row[self.output_field_in_lookup]))
                ranges.add_range(row[self.field_in_lookup], row[self.output_field_in_lookup])

        for record in records:
            if self.output_field not in record:
                record[self.output_field] = None
            if self.field not in record:
                continue
            if "-" not in record[self.field]:
                for lookup_range in ranges:
                    if record[self.field] in lookup_range:
                        if record[self.output_field] is None or self.overwrite:
                            record[self.output_field] = lookup_range[record[self.field]]
                        break
                yield record
            else:
                try:
                    range_min, range_max = map(int, record[self.field].split("-"))
                except:
                    raise ValueError(record[self.field])
                x = range_min

                while x <= range_max:
                    x_range = ranges.get_range(x)

                    # First, check if x is in a range
                    if x_range is not None:
                        # chunk_end, result_start, result_end = x_range.get_chunk(x)

                        if range_max <= x_range.range_max:
                            # our range is entirely within the lookup range
                            chunk_end = range_max
                            result_start = x_range[x]
                            result_end = x_range[chunk_end]
                        elif range_max > x_range.range_max:
                            # we start inside lookup range, end beyond it
                            chunk_end = x_range.range_max
                            result_start = x_range[x]
                            result_end = x_range.result_max

                        event = {}
                        event.update(record)
                        event.update({
                            self.field: f"{x}-{chunk_end}",
                            self.output_field: f"{result_start}-{result_end}",
                        })
                        # if self.field == "fertilizer":
                        #     raise ValueError(record)
                        yield event
                        x = chunk_end + 1
                        continue

                    x_range = ranges.find_next_range(x, range_max)
                    if x_range is not None:
                        # There's a future range that will match
                        event = {}
                        event.update(record)
                        event.update({
                            self.field: f"{x}-{x_range.range_min - 1}",
                            self.output_field: None
                        })
                        yield event
                        x = x_range.range_min
                        continue
                    else:
                        # No more ranges will match this range
                        event = {}
                        event.update(record)
                        event.update({
                            self.field: f"{x}-{range_max}",
                            self.output_field: None
                        })
                        yield event
                        break

dispatch(RangeLookupCommand, sys.argv, sys.stdin, sys.stdout, __name__)
