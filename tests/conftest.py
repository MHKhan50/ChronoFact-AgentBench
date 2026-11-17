import pandas as pd
import pytest


@pytest.fixture
def toy_frame():
    return pd.DataFrame(
        [
            {
                "SubjectID": "Q1", "RelationID": "P1", "ObjectID": "Q2",
                "SubjectLabel": "Example state", "RelationLabel": "leader",
                "ObjectLabel": "Person A", "StartDate": "2000-01-01",
                "EndDate": "2004-12-31", "Time": "2002",
                "Status": "Correct", "label": "correct", "granularity": "year",
                "fact_id": "Q1|P1|Q2", "Statement": "In 2002, who was the leader? Person A",
                "Alpha": 0.0,
            },
            {
                "SubjectID": "Q1", "RelationID": "P1", "ObjectID": "Q2",
                "SubjectLabel": "Example state", "RelationLabel": "leader",
                "ObjectLabel": "Person A", "StartDate": "2000-01-01",
                "EndDate": "2004-12-31", "Time": "1999",
                "Status": "Incorrect", "label": "incorrect", "granularity": "year",
                "fact_id": "Q1|P1|Q2", "Statement": "In 1999, who was the leader? Person A",
                "Alpha": -1.0,
            },
            {
                "SubjectID": "Q3", "RelationID": "P2", "ObjectID": "Q4",
                "SubjectLabel": "Example country", "RelationLabel": "president",
                "ObjectLabel": "Person B", "StartDate": "2010-06-15",
                "EndDate": "2012-03-10", "Time": "2010",
                "Status": "Transitional", "label": "transitional", "granularity": "year",
                "fact_id": "Q3|P2|Q4", "Statement": "In 2010, who was president? Person B",
                "Alpha": -0.2,
            },
            {
                "SubjectID": "Q5", "RelationID": "P3", "ObjectID": "Q6",
                "SubjectLabel": "Example company", "RelationLabel": "CEO",
                "ObjectLabel": "Person C", "StartDate": "2020-02-01",
                "EndDate": "2020-02-29", "Time": "2020-02",
                "Status": "Correct", "label": "correct", "granularity": "month",
                "fact_id": "Q5|P3|Q6", "Statement": "In February 2020, who was CEO? Person C",
                "Alpha": 0.0,
            },
        ]
    )
