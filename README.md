
# tentaclio-gsheets

A package containing all the dependencies for the gsheet tentaclio schema.

## Quick Start

This project comes with a `Makefile` which is ready to do basic common tasks

```
$ make help
install                       Initalise the virtual env installing deps
clean                         Remove all the unwanted clutter
lock                          Lock dependencies
update                        Update dependencies (whole tree)
sync                          Install dependencies as per the lock file
lint                          Lint files with flake and mypy
format                        Run black and isort
test                          Run unit tests
circleci                      Validate circleci configuration (needs circleci cli)
```


## Configuring access to google spreadsheets.

1. Get the credentials.
First we need a credentials file in order to be able to generate tokens.
click on enable google sheets api. Give the project a name of your choosing (eg `tentaclio`). Click on **APIs and services** -> **Credentials** -> **Create credentials** -> **Create OAuth client ID**, select **Desktop app** and **Download JSON**

2. Generate token file

```
pipenv install tentaclio && \
    pipenv run python -m tentaclio_gsheets google-token generate --credentials-file credentials.json
```
This will open a browser with a google auth page, log in and accept the authorisation request.
The token file has been saved in a default location '~/.tentaclio_google_sheets.json'. You can also configure this via the env variable `TENTACLIO__GSHEETS_TOKEN_FILE`

3. Get rid of credentials.json
The `credentials.json` file is no longer need, feel free to delete it.

# Usage

## Read google spreadsheet

The schema format to read a google spreadsheet is 
```
gsheets://{spreadsheet_id}/{Sheet name}
```


```python
import tentaclio

with tentaclio.open("gsheet://1Dfsfgdsgnfjksdnfsdjkfjkds/Sheet1") as f:
    print(f.read()) # read raw file
    df = pandas.read_csv(f) #read in dataframe
```

There is the option to exclude hidden columns/rows.

```python
import tentaclio

with tentaclio.open("gsheet://1Dfsfgdsgnfjksdnfsdjkfjkds/Sheet1", include_hidden_rows=False, include_hidden_columns=False) as f:
    print(f.read()) # read raw file
    df = pandas.read_csv(f) #read in dataframe

```

## Write google spreadsheet
In the same manner we can update values in spreadsheet - only overwrite

```python
import tentaclio

with tentaclio.open("gsheet://1Dfsfgdsgnfjksdnfsdjkfjkds/Sheet2",mode="w") as f:
    pandas.DataFrame({"a": [1,2,3], "b": [4,5,6]}).to_csv(f, index=False)
```



