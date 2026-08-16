# Jenkins Build Triage Report

- Logs directory: `logs`
- Builds analyzed: 7

## Status Summary

- **FAILURE**: 4
- **SUCCESS**: 2
- **UNKNOWN**: 1

## Root Cause Clusters

### Test Failure (2 builds)
- **build_4712** [Unit tests]: FAILED tests/unit/test_manifest_loader.py::test_acr_tag_derivation - AssertionError: expected tag derived from submodule SHA 'a41f9c', got 'latest'
- **build_4720** [Unit tests]: FAILED tests/unit/test_manifest_loader.py::test_acr_tag_derivation - AssertionError: expected tag derived from submodule SHA 'a41f9c', got 'latest'

### Dependency/Package Error (1 build)
- **build_4715** [Install dependencies]: ERROR: Cannot install pydantic==2.10.4 and pydantic-core==2.23.1 because these package versions have conflicting dependencies.

### Git/SCM Checkout Failure (1 build)
- **build_4718** [Checkout]: ERROR: Error fetching remote repo 'origin'

### Uncategorized (1 build)
- **build_4722** [Unit tests]: No specific error found (build did not report SUCCESS).

## Per-Build Details

| Build | Status | Stage | Reason |
|---|---|---|---|
| build_4711 | SUCCESS |  |  |
| build_4712 | FAILURE | Unit tests | FAILED tests/unit/test_manifest_loader.py::test_acr_tag_derivation - AssertionError: expected tag derived from submodule SHA 'a41f9c', got 'latest' |
| build_4715 | FAILURE | Install dependencies | ERROR: Cannot install pydantic==2.10.4 and pydantic-core==2.23.1 because these package versions have conflicting dependencies. |
| build_4718 | FAILURE | Checkout | ERROR: Error fetching remote repo 'origin' |
| build_4720 | FAILURE | Unit tests | FAILED tests/unit/test_manifest_loader.py::test_acr_tag_derivation - AssertionError: expected tag derived from submodule SHA 'a41f9c', got 'latest' |
| build_4722 | UNKNOWN | Unit tests | No specific error found (build did not report SUCCESS). |
| build_4725 | SUCCESS |  |  |