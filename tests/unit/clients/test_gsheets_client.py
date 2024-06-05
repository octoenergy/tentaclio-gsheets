from unittest.mock import MagicMock

import pytest

from tentaclio_gsheets.clients.gsheets_client import GoogleSheetsFsClient


@pytest.mark.parametrize(
    "include_hidden_columns, include_hidden_rows, expected_values",
    [
        (
            True,
            True,
            [
                ["name", "age", "job"],
                ["Dwight Schrute", "35", "Assistant to the Regional Manager"],
                ["Michael Scott", "45", "Regional Manager"],
                ["Jim Halpert", "30", "Salesman"],
                ["Pam Beesly", "30", "Receptionist"],
            ],
        ),
        (
            False,
            True,
            [
                ["age", "job"],
                ["35", "Assistant to the Regional Manager"],
                ["45", "Regional Manager"],
                ["30", "Salesman"],
                ["30", "Receptionist"],
            ],
        ),
        (
            False,
            False,
            [
                ["age", "job"],
                ["45", "Regional Manager"],
                ["30", "Salesman"],
                ["30", "Receptionist"],
            ],
        ),
        (
            True,
            False,
            [
                ["name", "age", "job"],
                ["Michael Scott", "45", "Regional Manager"],
                ["Jim Halpert", "30", "Salesman"],
                ["Pam Beesly", "30", "Receptionist"],
            ],
        ),
    ],
)
def test_drop_hidden(
    mock_gsheet_api_values,
    mock_gsheets_metadata,
    include_hidden_columns,
    include_hidden_rows,
    expected_values,
):
    client = GoogleSheetsFsClient(
        "gsheet://dunder-mifflin/dwight-schrute-range",
        include_hidden_rows=include_hidden_rows,
        include_hidden_columns=include_hidden_columns,
    )
    client._service = MagicMock()
    client._service.get.return_value.execute.return_value = mock_gsheets_metadata
    values = client._drop_hidden(mock_gsheet_api_values)
    assert len(values) == len(expected_values)
    assert all([a == b for a, b in zip(values, expected_values)])


def test_prepare_to_csv(mock_gsheet_api_values, mock_gsheets_metadata):
    client = GoogleSheetsFsClient("gsheet://dunder-mifflin/dwight-schrute-range")
    client._service = MagicMock()
    client._service.get.return_value.execute.return_value = mock_gsheets_metadata
    reader = client._prepare_to_csv(mock_gsheet_api_values)
    assert (
        reader.read()
        == "name,age,job\r\nDwight Schrute,35,Assistant to the Regional Manager\r\nMichael Scott,45,Regional Manager\r\nJim Halpert,30,Salesman\r\nPam Beesly,30,Receptionist\r\n"  # noqa
    )


def test_put(mock_gsheet_api_values, mock_gsheets_metadata):
    client = GoogleSheetsFsClient("gsheet://dunder-mifflin/dwight-schrute-range")
    client._service = MagicMock()
    client._service.values().update.return_value.execute.return_value = None
    client._service.get.return_value.execute.return_value = mock_gsheets_metadata
    client._write_to_gsheets(mock_gsheet_api_values)
    client._service.values().update.assert_called_once_with(
        spreadsheetId="dunder-mifflin",
        range="dwight-schrute-range",
        valueInputOption="USER_ENTERED",
        body={"values": mock_gsheet_api_values},
    )
