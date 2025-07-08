# CLI Command Audit Matrix

| Command                  | Key Options/Flags                                              | In README | In Memory-Bank | All Options Documented | Notes                                    |
|--------------------------|---------------------------------------------------------------|-----------|---------------|-----------------------|------------------------------------------|
| geometric                | --bbox, --recreate-db, --save-as-temp                         | Y         | Y             | Partial               | --save-as-temp rarely documented         |
| fast-enrich              | --batch-size, --limit                                         | Y         | Y             | Partial               | --batch-size sometimes missing           |
| incremental-enrich       | --batch-size, --days-old, --limit                             | Y         | Partial       | Partial               | --days-old sometimes missing             |
| full-refresh             | --batch-size, --limit                                         | Y         | N             | N                     | Not in memory-bank                       |
| delta-enrich             | --batch-size, --limit, --fresh-table, --auto-geometric, --show-details | Y         | N             | Partial               | --show-details, --fresh-table missing    |
| smart-pipeline           | --geometric-first, --batch-size, --bbox                       | Y         | Y             | Partial               | DB-driven orchestration now standard     |
| monitor                  | status, recommend, schedule-info                              | Y         | N             | Partial               | Only status/recommend in memory-bank     |
| province-geometric       | province, --strategy, --recreate-db, --save-as-temp           | Y         | Y             | Partial               | DB-driven, province-wide runs supported  |
| saudi-arabia-geometric   | --strategy, --recreate-db, --save-as-temp                     | Y         | Y             | Partial               | DB-driven, all-province runs supported   |
| discovery-summary        | (none)                                                        | Y         | Y             | Y                     | DB-driven summary                        |
| province-pipeline        | province, --strategy, --batch-size, --geometric-first         | Y         | Y             | Partial               | DB-driven, province-wide runs supported  |
| saudi-pipeline           | --strategy, --batch-size, --geometric-first                   | Y         | Y             | Partial               | DB-driven, all-province runs supported   |

Legend:
- Y = Yes, N = No, Partial = Some options/flags are missing or outdated

## Immediate Recommendations
- All province/all-province commands are now DB-driven. Remove any references to legacy tile discovery commands.
- Ensure all options/flags are documented for each command.
- Standardize command syntax (remove old subcommand patterns).
- Add usage examples for advanced and composite commands.
- Review and update help text in CLI for clarity and completeness. 