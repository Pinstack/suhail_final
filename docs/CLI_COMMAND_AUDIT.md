# CLI Command Audit Matrix

| Command                  | Key Options/Flags                                              | In README | In Memory-Bank | All Options Documented | Notes                                    |
|--------------------------|---------------------------------------------------------------|-----------|---------------|-----------------------|------------------------------------------|
| geometric                | --bbox, --recreate-db, --save-as-temp                         | Y         | Y             | Partial               | --save-as-temp rarely documented         |
| fast-enrich              | --batch-size, --limit                                         | Y         | Y             | Partial               | --batch-size sometimes missing           |
| incremental-enrich       | --batch-size, --days-old, --limit                             | Y         | Partial       | Partial               | --days-old sometimes missing             |
| full-refresh             | --batch-size, --limit                                         | Y         | N             | N                     | Not in memory-bank                       |
| delta-enrich             | --batch-size, --limit, --fresh-table, --auto-geometric, --show-details | Y         | N             | Partial               | --show-details, --fresh-table missing    |
| smart-pipeline           | --geometric-first, --batch-size, --bbox                       | N         | N             | N                     | Not documented                           |
| monitor                  | status, recommend, schedule-info                              | Y         | N             | Partial               | Only status/recommend in memory-bank     |
| province-geometric       | province, --strategy, --recreate-db, --save-as-temp           | N         | N             | N                     | Not documented                           |
| saudi-arabia-geometric   | --strategy, --recreate-db, --save-as-temp                     | N         | N             | N                     | Not documented                           |
| discovery-summary        | (none)                                                        | N         | N             | N                     | Not documented                           |
| province-pipeline        | province, --strategy, --batch-size, --geometric-first         | N         | N             | N                     | Not documented                           |
| saudi-pipeline           | --strategy, --batch-size, --geometric-first                   | N         | N             | N                     | Not documented                           |

Legend:
- Y = Yes, N = No, Partial = Some options/flags are missing or outdated

## Immediate Recommendations
- Update README and memory-bank to include all commands, especially advanced/province/country-wide workflows.
- Ensure all options/flags are documented for each command.
- Standardize command syntax (remove old subcommand patterns).
- Add usage examples for advanced and composite commands.
- Review and update help text in CLI for clarity and completeness. 