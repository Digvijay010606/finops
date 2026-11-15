# Data Quality Report
Rows validated: 27,150
Passed: 26,908  Quarantined: 242 (0.89%)

| Rule | Rows |
|---|---|
| DUPLICATE_LINE_ITEM | 150 |
| NULL_RESOURCE_ID | 80 |
| NEGATIVE_COST | 12 |

Schema drift columns detected at ingest: ['lineItem/LegalEntity']
Costs imputed from qty x rate: 199
Untagged env/team/owner rows: 4029/4040/3233