# Slowest Tests (Top 25)


| Rank | Test | Duration (s) |
|---:|---|---:|
| 1 | `call     tests/test_workflows_e2e.py::test_full_inbox_drive_sweep_workflow` | 3.450 |
| 2 | `call     tests/test_integration_djp.py::test_djp_workflow_with_real_corpus` | 2.890 |
| 3 | `call     tests/test_nightshift_e2e.py::test_nightshift_full_workflow` | 2.670 |
| 4 | `call     tests/test_integration_grounded.py::test_grounded_workflow_full_chain` | 2.340 |
| 5 | `call     tests/test_orchestrator_runner.py::test_dag_with_checkpoints_and_recovery` | 1.980 |
| 6 | `call     tests/test_connector_ingest_path.py::test_full_ingest_pipeline_slack` | 1.870 |
| 7 | `call     tests/test_graph_search.py::test_urg_search_with_large_corpus` | 1.760 |
| 8 | `call     tests/test_persistent_queue.py::test_queue_with_redis_backend` | 1.650 |
| 9 | `call     tests/test_templates_batch.py::test_batch_render_100_templates` | 1.540 |
| 10 | `call     tests/test_openai_adapter.py::test_swarm_integration_with_tools` | 1.430 |
| 11 | `call     tests/test_gmail_connector_resilience.py::test_gmail_retry_with_backoff` | 1.320 |
| 12 | `call     tests/test_notion_connector_resilience.py::test_notion_rate_limit_handling` | 1.280 |
| 13 | `call     tests/test_slack_connector_resilience.py::test_slack_webhook_validation` | 1.210 |
| 14 | `call     tests/test_lifecycle.py::test_storage_tier_migration_full_cycle` | 1.150 |
| 15 | `call     tests/test_autoscaler.py::test_worker_pool_scale_up_and_down` | 1.090 |
| 16 | `call     tests/test_compliance_export.py::test_full_compliance_export_workflow` | 1.050 |
| 17 | `call     tests/test_blue_green.py::test_blue_green_deployment_full_cycle` | 0.980 |
| 18 | `call     tests/test_keyring.py::test_key_rotation_with_re_encryption` | 0.950 |
| 19 | `call     tests/test_graph_index.py::test_urg_index_batch_insert_1000_nodes` | 0.890 |
| 20 | `call     tests/test_state_store.py::test_checkpoint_recovery_with_large_state` | 0.840 |
| 21 | `call     tests/test_audit.py::test_audit_log_pagination_1000_events` | 0.790 |
| 22 | `call     tests/test_budgets.py::test_budget_enforcement_across_tenants` | 0.760 |
| 23 | `call     tests/test_nlp_planner.py::test_nl_command_planning_with_contacts` | 0.720 |
| 24 | `call     tests/test_corpus.py::test_corpus_load_large_dataset` | 0.680 |
| 25 | `call     tests/test_redaction.py::test_redaction_with_pii_detection` | 0.650 |

**Total measured duration:** 35.94s across 25 timed tests.
