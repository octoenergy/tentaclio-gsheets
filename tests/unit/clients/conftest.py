import pytest


@pytest.fixture
def mock_gsheet_url():
    return "gsheet://dunder-mifflin/dwight-schrute-range"


@pytest.fixture
def mock_gsheet_api_values():
    return [
        ["name", "age", "job"],
        ["Dwight Schrute", "35", "Assistant to the Regional Manager"],
        ["Michael Scott", "45", "Regional Manager"],
        ["Jim Halpert", "30", "Salesman"],
        ["Pam Beesly", "30", "Receptionist"],
    ]


@pytest.fixture
def mock_gsheets_metadata():
    return {
        "sheets": [
            {
                "properties": {
                    "title": "Sheet1",
                    "gridProperties": {
                        "rowCount": 1000,
                        "columnCount": 26,
                    },
                },
                "data": [
                    {
                        "columnMetadata": [
                            {
                                "pixelSize": 21,
                                "hiddenByUser": True,
                            },
                            {
                                "pixelSize": 21,
                            },
                            {
                                "pixelSize": 21,
                            },
                        ],
                        "rowMetadata": [
                            {
                                "pixelSize": 21,
                            },
                            {
                                "pixelSize": 21,
                                "hiddenByUser": True,
                            },
                            {
                                "pixelSize": 21,
                            },
                            {
                                "pixelSize": 21,
                            },
                            {
                                "pixelSize": 21,
                            },
                        ],
                    }
                ],
            }
        ]
    }
