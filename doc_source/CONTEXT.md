# doc_source

Parent: [../CONTEXT.md](../CONTEXT.md)

## Purpose

The `doc-source` mode: `GHDocSourceCollector` and its repository entry. Its behaviour is [README.md](README.md);
this file maps that page to the code.

Not responsible for: file discovery, the metadata envelope and writing the artifact (`utils/`, the root
`CONTEXT.md`); parsing headers, statuses and relations (`living_doc_utilities.authoring`).

## Code map

What realises each fact of [README.md](README.md), the mode's page:

- The mode mines local checkouts into one `doc-source-v1.0.0` artifact → `doc_source/collector.py::GHDocSourceCollector`
- `doc-source: true` turns it on → `action_inputs.py::ActionInputs.is_doc_source_mode_enabled`
- User Stories from `.feature` files under `us-paths` → `doc_source/collector.py::GHDocSourceCollector._collect_feature_file`
- Functionalities from `.feature` files under `func-paths` → `doc_source/collector.py::GHDocSourceCollector._collect_feature_file`
- Features from PageObject header comments under `pages-paths` → `doc_source/collector.py::GHDocSourceCollector._collect_page_object`
- Each entry is one source; a malformed entry fails the run at start → `doc_source/model/config_repository.py::ConfigRepository.load_from_json`
- `us-paths` or its alias `paths` is required; the other path fields are optional → `utils/utils.py::get_path_list`
- One check of the two names for both modes → `utils/utils.py::check_repository_names`
- A missing configured path fails its whole source → `utils/feature_file_discovery.py::discover_feature_files`
- Discovery is recursive → `utils/feature_file_discovery.py::discover_ts_files`
- `.feature` files under a `tutorial*` directory are skipped → `utils/feature_file_discovery.py::_is_under_tutorial_dir`
- A `.feature` file with no living-doc header is `MISSING_ENTITY_ID`, not emitted → `doc_source/collector.py::GHDocSourceCollector._add_entity`
- A `.ts` file with no `LIVING DOC` text is skipped silently → `doc_source/collector.py::_has_living_doc_header`
- The first block comment of a `.ts` file is its header → `doc_source/collector.py::GHDocSourceCollector._collect_page_object`
- The output file name → `doc_source/collector.py::DOC_SOURCE_FILE_NAME`
- Written through `write_artifact`: validated, then written atomically → `utils/artifact.py::store_artifact`
- What the mode fills in the contract → `doc_source/collector.py::GHDocSourceCollector.build_result`
- `source_ref`, its permalink and `NO_SOURCE_URL` → `utils/artifact.py::build_source_ref`
- A cross-reference PageObject header adds its page to its Feature → `doc_source/collector.py::GHDocSourceCollector._attach_cross_references`
- A configured path with no matching files logs a warning → `utils/feature_file_discovery.py::discover_feature_files`
- `EMPTY_SOURCE` when nothing in the source is read as a header → `doc_source/collector.py::_Collected.answered`
- An unreadable file is logged and skipped → `doc_source/collector.py::_read`
- No living-doc header or no parseable entity id: `MISSING_ENTITY_ID` → `doc_source/collector.py::GHDocSourceCollector._add_entity`
- An entity id already collected: `AUTHORING_ERROR`, the first file keeps it → `doc_source/collector.py::GHDocSourceCollector._add_entity`
- An entity the contract rejects: `AUTHORING_ERROR`, derived without it → `doc_source/collector.py::GHDocSourceCollector._derive_accepted`
- A cross-reference page whose Feature is not in the run: `UNRESOLVED_RELATION` → `doc_source/collector.py::GHDocSourceCollector._attach_cross_references`
- The `authoring` parsers' warnings on malformed headers → `doc_source/collector.py::GHDocSourceCollector._collect_feature_file`
- A result that fails validation or cannot be written fails the mode → `utils/artifact.py::collect_artifact`
- A warning about one file carries its `path` → `utils/artifact.py::with_path`
- A warning with a `path` carries the file's `source_url` → `utils/artifact.py::file_url`
- `MISSING_STATUS` and `STATUS_AC_MISMATCH` carry the entity's file in `path` → `utils/artifact.py::with_entity_paths`
- A dropped cross-reference page's `UNRESOLVED_RELATION` carries `path` and `context` → `doc_source/collector.py::GHDocSourceCollector._attach_cross_references`
- `derive_statuses` and `check_relations` run once per run over all sources → `doc_source/collector.py::GHDocSourceCollector.build_result`
