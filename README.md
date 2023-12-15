# Instructions

## Prerequisites

In order to make full use of this app, you must have registered for Advent of Code. You can use the
example data without registering, however.

## Install

This app should be installed only on a Splunk Search Head. You will not need to restart Splunk after installing the app.

## Configuration

There is no additional configuration necessary for this app. However, if you wish to use the app with
your own input data, those must be downloaded and formatted correctly into lookups in the app. Unless specified in day-specific instructions, follow these instructions to load your personal input data:

1. Download your input data for each day and save it in this app's lookup directory.
2. This app contains example data for each puzzle, stored in `YYYY-DD_example.csv`. Your input data should be
   stored in `YYYY-DD_input.csv`, where `YYYY` is the 4-digit year and `NN` is the zero-padded day of the month.
3. You will need to add a header row to your input data as well. Use the header row (first row in the file)
   from the example data CSV.

## Special Setup

Some days require additional setup instructions. This section will outline the necessary steps

### 2022 Day 2: Calorie Counting

1. Follow general instructions for loading input data.
2. Replace all spaces in input data with commas.
3. See `lookups/2022-02_example.csv` for proper formatting.

### 2022 Day 5: Supply Stacks

Input data needs to be split into two separate lookup files for day 5. See `lookups/2022-05_example_seed.csv`
and `lookups/2022-05_example_procedure.csv` for examples of the formatting.

#### 2022-05_input_seed.csv

This lookup contains the "drawing" referred to in the instructions. It will look something like this:

```
    [D]
[N] [C]
[Z] [M] [P]
 1   2   3
```

This needs to be converted to a CSV, which will look like this:

```
stack_1,stack_2,stack_3
,[D],
[N],[C],
[Z],[M],[P]
```

#### 2022-05_input_procedure.csv

This lookup is all of the instructions following the "drawing" in the input data. All rows will contain
a single column, and the header for this column is "procedure".

# Known Issues

There are no known issues at this time.

# Upgrade

No special instructions for upgrading this app to a newer version.

# Help

While this app is not formally supported, the developer can be reached at smcmaster@splunk.com (OR in splunk-usergroups slack, @iamthemcmaster). Responses are made on a best effort basis. Feedback is always welcome and appreciated!

Learn more about splunk-usergroups slack here: https://docs.splunk.com/Documentation/Community/current/community/Chat#Join_us_on_Slack
