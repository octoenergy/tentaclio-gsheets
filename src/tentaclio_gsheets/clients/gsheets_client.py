"""Google sheets client."""

import csv
import io
import json
import logging
import os
import platform
from typing import List, Optional, Union

import pandas as pd
import tentaclio
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_default_token_file():
    """Get default token file path.

    Includes a fallback of the current working directory.
    If the user profile environment variables are not set.
    """
    if "windows" in platform.system().lower():
        HOME = os.environ.get("UserProfile")
    else:
        HOME = os.environ.get("HOME")

    if not HOME:
        HOME = os.getcwd()

    return HOME + os.sep + ".tentaclio_google_sheets.json"


DEFAULT_TOKEN_FILE = _get_default_token_file()

TOKEN_FILE = os.getenv("TENTACLIO__GSHEETS_TOKEN_FILE", DEFAULT_TOKEN_FILE)


class GoogleSheetsFsClient(
    tentaclio.clients.base_client.BaseClient["GoogleSheetsFsClient"]
):
    """Google sheets client

    Ref: https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets
    """

    allowed_schemes = ["gsheet", "gsheets"]

    def __init__(
        self,
        url: str,
        header: Optional[bool] = True,
        include_hidden_columns: Optional[bool] = True,
        include_hidden_rows: Optional[bool] = True,
    ) -> None:
        """
        Create new gsheets client.

        The client is based on a url that contains the spreadsheet id and the cell range
        in the following format: gsheet://spreadsheet_id/cell_range
        """

        super().__init__(url)
        self.include_hidden_columns = include_hidden_columns
        self.include_hidden_rows = include_hidden_rows
        self.header = header

    @property
    def cell_range(self) -> str:
        return self.url.path[1:]

    @property
    def sheet_id(self) -> str:
        return self.url.url.split("/")[2]

    def _connect(self) -> tentaclio.Closable:

        self._service = build(
            "sheets",
            "v4",
            credentials=load_credentials(TOKEN_FILE),
            cache_discovery=False,
        ).spreadsheets()

    def close(self) -> None:
        self._service = None

    def _get_metadata(self) -> Union[dict, None]:
        """
        Retrieves the metadata of the spreadsheet.

        Returns:
            Union[dict, None]: The metadata of the spreadsheet if it exists, otherwise None.
        """
        try:
            metadata = self._service.get(
                spreadsheetId=self.sheet_id,
                ranges=self.cell_range,
                includeGridData=True,
            ).execute()["sheets"][0]["data"][0]
        except IndexError as e:
            logger.warning(f"Sheet {self.sheet_id} has no metadata - {e}")
            return None

        return metadata

    def _get_values(self) -> List[List[str]]:
        """Gets the values of the sheet

        Returns:
            List[List[str]]: the list of values of the sheet

        """

        result = (
            self._service.values()
            .get(spreadsheetId=self.sheet_id, range=self.cell_range)
            .execute()
        )
        values = result.get("values", [])

        return values

    def _get_hidden(self) -> dict:
        """
        Retrieves the hidden rows and columns metadata from the Google Sheets API.

        Returns:
            dict: A dictionary containing the hidden rows and columns metadata.
            The dictionary has the following structure:
            {
                "row_metadata": [bool],
                "column_metadata": [bool]
            }
        """
        if (metadata := self._get_metadata()) is None:
            return {}

        hidden_columns = [
            col.get("hiddenByUser", None) is not None
            for col in metadata.get("columnMetadata", [])
        ]
        hidden_rows = [
            row.get("hiddenByUser", None) is not None
            for row in metadata.get("rowMetadata", [])
        ]

        return {"row_metadata": hidden_rows, "column_metadata": hidden_columns}

    def _drop_hidden(self, values: List[List[str]]) -> List[List[str]]:
        """
        Drops hidden rows and columns from the given values.

        Args:
            values (List[List[str]]): The input values containing hidden rows and columns.

        Returns:
            List[List[str]]: The modified values with hidden rows and columns removed.
        """
        hidden = self._get_hidden()

        if not self.include_hidden_columns:
            values = [
                [
                    value
                    for value, hidden in zip(row, hidden["column_metadata"])
                    if not hidden
                ]
                for row in values
            ]

        if not self.include_hidden_rows:
            values = [
                row for row, hidden in zip(values, hidden["row_metadata"]) if not hidden
            ]

        return values

    def _prepare_to_csv(self, values: List[List[str]]) -> io.StringIO:
        """
        Prepares the given values as a CSV file.

        Args:
            values (List[List[str]]): The values to be converted to CSV.

        Returns:
            io.StringIO: A StringIO object containing the CSV data.
        """
        output = io.StringIO()
        values = self._drop_hidden(values)
        writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        for row in values:
            writer.writerow(row)
        output.seek(0)
        return output

    def _write_to_gsheets(self, values: List[List[str]]) -> None:
        """
        Writes the given values to a Google Sheets spreadsheet.

        Args:
            values (List[List[str]]): The values to be written to the spreadsheet.

        Returns:
            None
        """
        body = {"values": values}
        self._service.values().update(
            spreadsheetId=self.sheet_id,
            range=self.cell_range,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()

    @tentaclio.decorators.check_conn
    def get(self, writer: tentaclio.protocols.ByteWriter) -> None:
        result = self._prepare_to_csv(self._get_values())
        writer.write(result.read().encode("utf-8"))

    @tentaclio.decorators.check_conn
    def put(self, reader: tentaclio.protocols.ByteReader) -> None:

        reader = io.StringIO(reader.read().decode())
        csv_reader = csv.reader(reader, delimiter=",", quoting=csv.QUOTE_MINIMAL)

        values = [row for row in csv_reader]

        self._write_to_gsheets(values)


def load_credentials(token_file: str) -> Credentials:
    """Load the credentials and refresh them if necesary."""
    creds = None
    if os.path.exists(token_file):
        with open(token_file) as f:
            state = json.load(f)
            state["expiry"] = pd.to_datetime(state["expiry"]).replace(tzinfo=None)
            creds = Credentials(**state)
    else:
        raise ValueError(f"Token file is not valid {token_file}")

    # If there are no (valid) credentials available refresh them or raise an error.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise ValueError(f"Couldn't refresh token in f{token_file}")
        # Save the credentials for the next run
        with open(token_file, "w") as f:
            f.write(creds.to_json())
    return creds
