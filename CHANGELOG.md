# Changelog

## [3.0.0](https://github.com/fdmorison/tiozin/compare/tiozin-v2.0.0...tiozin-v3.0.0) (2026-04-26)


### ⚠ BREAKING CHANGES

* **core:** Default treats only None as unset and is now recursive ([#201](https://github.com/fdmorison/tiozin/issues/201))
* **core:** Registry contract to allow domain-specific APIs ([#199](https://github.com/fdmorison/tiozin/issues/199))
* **core:** Add "auto" schema subject and opt-in schema lookup ([#193](https://github.com/fdmorison/tiozin/issues/193))
* **core:** Expose registries in Context ([#164](https://github.com/fdmorison/tiozin/issues/164))
* **core:** Rename core components ([#163](https://github.com/fdmorison/tiozin/issues/163))
* **core:** Reduce DAY template aliases ([#162](https://github.com/fdmorison/tiozin/issues/162))
* **core:** Simplify TiozinApp lifecycle ([#159](https://github.com/fdmorison/tiozin/issues/159))
* **core:** Add YAML utilities to tiozin.utils.io ([#158](https://github.com/fdmorison/tiozin/issues/158))
* **core:** Integrate Settings System into TiozinApp, Lifecycle, and CLI ([#151](https://github.com/fdmorison/tiozin/issues/151))
* **core:** Rename @self token to @data ([#142](https://github.com/fdmorison/tiozin/issues/142))
* **core:** ImproveTemplateDate fluent interface ([#136](https://github.com/fdmorison/tiozin/issues/136))
* **core:** Review exception model and introduce retryable support ([#135](https://github.com/fdmorison/tiozin/issues/135))
* **core:** Introduce subdomain field ([#129](https://github.com/fdmorison/tiozin/issues/129))
* **core:** Redesign Context execution model to align with Python context management ([#126](https://github.com/fdmorison/tiozin/issues/126))
* **core:** Adopt Tiozin and Tio naming across the codebase ([#125](https://github.com/fdmorison/tiozin/issues/125))

### Features

* **core:** Add "auto" schema subject and opt-in schema lookup ([#193](https://github.com/fdmorison/tiozin/issues/193)) ([b7babb9](https://github.com/fdmorison/tiozin/commit/b7babb9d76ec1a35d148337ad0ab3aaddf25ba1a))
* **core:** Add classproperty decorator and refine tioproxy internals ([#124](https://github.com/fdmorison/tiozin/issues/124)) ([c17f779](https://github.com/fdmorison/tiozin/commit/c17f779c3f7fd079344df889817fdac225994522))
* **core:** Add Context.render ([#174](https://github.com/fdmorison/tiozin/issues/174)) ([83176b7](https://github.com/fdmorison/tiozin/commit/83176b7f1cce7889c666b808e0643cadc0881e79))
* **core:** Add deterministic .env resolution order ([#110](https://github.com/fdmorison/tiozin/issues/110)) ([3827a79](https://github.com/fdmorison/tiozin/commit/3827a79e3f4b4902e78581fe83676391be1b8197))
* **core:** Add HTTP, HTTPS, FTP, and SFTP support via fsspec extras ([#155](https://github.com/fdmorison/tiozin/issues/155)) ([9ba2a86](https://github.com/fdmorison/tiozin/commit/9ba2a86f3af0dd0d99fe0062cefe1db8816cfd19))
* **core:** Add job namespace and rename step lineage method ([#175](https://github.com/fdmorison/tiozin/issues/175)) ([f7849b5](https://github.com/fdmorison/tiozin/commit/f7849b559f0e92d2929aff340f2c57f09b14749a))
* **core:** Add Open Lineage system ([#170](https://github.com/fdmorison/tiozin/issues/170)) ([ba95dae](https://github.com/fdmorison/tiozin/commit/ba95dae8207d0acac33f107b2b33338d5c91309b))
* **core:** Add RegistryProxy with template rendering ([#153](https://github.com/fdmorison/tiozin/issues/153)) ([615ffd5](https://github.com/fdmorison/tiozin/commit/615ffd59f9ba48592caaba40a73c6016092a5730))
* **core:** Add secret management system ([#166](https://github.com/fdmorison/tiozin/issues/166)) ([cbdb0ca](https://github.com/fdmorison/tiozin/commit/cbdb0ca74c4833f20f3d4de94cf1d9a9e856b14a))
* **core:** Add Setting System with Registry and Manifest ([#150](https://github.com/fdmorison/tiozin/issues/150)) ([15b0d92](https://github.com/fdmorison/tiozin/commit/15b0d9259aad4a6b82a9ee3d0534c69e2af1f625))
* **core:** Add slug to Tiozin and Context for safe SQL/filesystem identifier ([#128](https://github.com/fdmorison/tiozin/issues/128)) ([80173e1](https://github.com/fdmorison/tiozin/commit/80173e17d826994c72d61615c46133b81547b541))
* **core:** Add validate command ([#160](https://github.com/fdmorison/tiozin/issues/160)) ([ec08dcc](https://github.com/fdmorison/tiozin/commit/ec08dcc261f65edabb015a754298fcba1d6fcd58))
* **core:** Add YAML utilities to tiozin.utils.io ([#158](https://github.com/fdmorison/tiozin/issues/158)) ([31db279](https://github.com/fdmorison/tiozin/commit/31db279ca51be5c703815d088a73df268641a6d2))
* **core:** cli run accepts multiple jobs ([#161](https://github.com/fdmorison/tiozin/issues/161)) ([1065c9f](https://github.com/fdmorison/tiozin/commit/1065c9f9320f14abf2cf1b4153a976ceac6e1e77))
* **core:** Emit input dataset schemas in OpenLineage events ([#182](https://github.com/fdmorison/tiozin/issues/182)) ([455940a](https://github.com/fdmorison/tiozin/commit/455940a2ecf0b724310bd2a09b6cc80871cfcd5d))
* **core:** Enable step lineage and fix runtime bugs ([#184](https://github.com/fdmorison/tiozin/issues/184)) ([be0aef5](https://github.com/fdmorison/tiozin/commit/be0aef502bb63639f3e49b208889f03d45d037fc))
* **core:** Expose registries in Context ([#164](https://github.com/fdmorison/tiozin/issues/164)) ([4a970e9](https://github.com/fdmorison/tiozin/commit/4a970e96d9eb8aa7881a20a40920566ef998cca5))
* **core:** ImproveTemplateDate fluent interface ([#136](https://github.com/fdmorison/tiozin/issues/136)) ([1091b0f](https://github.com/fdmorison/tiozin/commit/1091b0f3f086c4ba1797ddbd627571fd37107c0d))
* **core:** Introduce dataset lineage tracking ([#171](https://github.com/fdmorison/tiozin/issues/171)) ([8f80c51](https://github.com/fdmorison/tiozin/commit/8f80c514f66bf463984301325fa932f31fc022ec))
* **core:** Introduce Schema System ([#179](https://github.com/fdmorison/tiozin/issues/179)) ([696677d](https://github.com/fdmorison/tiozin/commit/696677d9c5e760586c6a3beb5304b4b66e0350ae))
* **core:** Introduce subdomain field ([#129](https://github.com/fdmorison/tiozin/issues/129)) ([ec2e9b6](https://github.com/fdmorison/tiozin/commit/ec2e9b69ff047ffb487876e942a2bc7f22921a42))
* **core:** Strip glob and partition from lineage dataset paths ([#178](https://github.com/fdmorison/tiozin/issues/178)) ([9e9b850](https://github.com/fdmorison/tiozin/commit/9e9b850e3f7b4c9afbc10a19efad110f91a51e56))
* **tio_duckdb:** Expand DuckdbFileInput to support advanced read scenarios ([#114](https://github.com/fdmorison/tiozin/issues/114)) ([ede001f](https://github.com/fdmorison/tiozin/commit/ede001fb80e2222b866dd3d3449e33fdad0f5a24))
* **tio_duckdb:** Introduce DuckdbPostgresOutput ([#144](https://github.com/fdmorison/tiozin/issues/144)) ([a503d0e](https://github.com/fdmorison/tiozin/commit/a503d0e714b30b64668d4fa3623fa61b4a3bb3ba))
* **tio_duckdb:** Tio DuckDB provider with Runner, Inputs, Outputs, SQL Transforms, and declarative job examples ([#113](https://github.com/fdmorison/tiozin/issues/113)) ([7902b31](https://github.com/fdmorison/tiozin/commit/7902b31f32e99672fe4f9e69e09ad82ef8e017ae))
* **tio_kernel:** Add location as base directory for FileJobRegistry ([#156](https://github.com/fdmorison/tiozin/issues/156)) ([1a9c21a](https://github.com/fdmorison/tiozin/commit/1a9c21ab5aabfb4c8dcd54dc590e28e70434254c))
* **tio_spark:** Introduce provider-level proxies and SQL-first Spark pipelines ([#108](https://github.com/fdmorison/tiozin/issues/108)) ([9a33fe9](https://github.com/fdmorison/tiozin/commit/9a33fe924af5a754b110511e148ea69b71220dfa))


### Bug Fixes

* **core:** Allow [@tioproxy](https://github.com/tioproxy) to accept multiple proxies and reject stacking ([#123](https://github.com/fdmorison/tiozin/issues/123)) ([8939b7b](https://github.com/fdmorison/tiozin/commit/8939b7bf0712e3de4218fd6d0440248805a9e593))
* **core:** Enforce failfast when registries raise NotFoundError ([#200](https://github.com/fdmorison/tiozin/issues/200)) ([bfaec11](https://github.com/fdmorison/tiozin/commit/bfaec114d176bd419b986efcbc47706f68225036))
* **core:** Fix settings delegation and registry configuration ([#152](https://github.com/fdmorison/tiozin/issues/152)) ([affb94e](https://github.com/fdmorison/tiozin/commit/affb94ed215c2f86a5ef89163af1215ffebacca3))
* **core:** Template rendering in plugin setup and teardown ([#115](https://github.com/fdmorison/tiozin/issues/115)) ([6aa4d80](https://github.com/fdmorison/tiozin/commit/6aa4d802fcfc058258d1749177d2a381d3b3cf97))
* **security:** Secret leakage and run_id format ([#132](https://github.com/fdmorison/tiozin/issues/132)) ([f54fe65](https://github.com/fdmorison/tiozin/commit/f54fe65490fc498efbf25db4161b893bef27f6ce))
* **tio_spark:** Capture output schema in write() when result is not a DataFrame ([#185](https://github.com/fdmorison/tiozin/issues/185)) ([d25fa6b](https://github.com/fdmorison/tiozin/commit/d25fa6b73f6ece41256b65f6a0439fbcb618c985))


### Documentation

* Add complete ETL example and clarify state rules in tiozins guide ([#148](https://github.com/fdmorison/tiozin/issues/148)) ([aadccdd](https://github.com/fdmorison/tiozin/commit/aadccdd626fbc0015bfb5c26b2af97e23c180f58))
* Add how-to guides for OpenLineage, schemas and secrets ([#195](https://github.com/fdmorison/tiozin/issues/195)) ([8d4ce16](https://github.com/fdmorison/tiozin/commit/8d4ce162eec6d79e1414bae7653391e4f7bc8dbe))
* Add Marquez screenshot and tiozin.yaml labels to OpenLineage guide ([#196](https://github.com/fdmorison/tiozin/issues/196)) ([3875775](https://github.com/fdmorison/tiozin/commit/38757757c08394a2f847411ae25ce664293cfe30))
* Add Settings Reference ([#154](https://github.com/fdmorison/tiozin/issues/154)) ([f96c686](https://github.com/fdmorison/tiozin/commit/f96c6867273d40c75e778ff012801d2690faeda9))
* Add Template Reference ([#138](https://github.com/fdmorison/tiozin/issues/138)) ([139c1e9](https://github.com/fdmorison/tiozin/commit/139c1e92f963ba16b278e2ebe14826121375ffab))
* **core:** Add ADR 0002 about separate step type classes ([#194](https://github.com/fdmorison/tiozin/issues/194)) ([fb9b377](https://github.com/fdmorison/tiozin/commit/fb9b37721ecfaf99ae3b0b2b33a0f7acfe66d306))
* **core:** Restructure extending section ([#177](https://github.com/fdmorison/tiozin/issues/177)) ([303157b](https://github.com/fdmorison/tiozin/commit/303157b36520491b00600d6815184674f5c02bd0))
* Fix documentation inconsistencies and style issues ([#147](https://github.com/fdmorison/tiozin/issues/147)) ([e3c8538](https://github.com/fdmorison/tiozin/commit/e3c8538475df62480aa7fb4dfa83d134b6325a2f))
* Improve README and write about Tiozin Family model ([#118](https://github.com/fdmorison/tiozin/issues/118)) ([5903943](https://github.com/fdmorison/tiozin/commit/59039438dfaaab58dd336f2ae0ecf5bddc7c7926))
* Improves README and documentation index ([#133](https://github.com/fdmorison/tiozin/issues/133)) ([7b70fa3](https://github.com/fdmorison/tiozin/commit/7b70fa3ae56c3dccad974ae135ae05580e7bd862))
* Initial agent specification and test agent ([#139](https://github.com/fdmorison/tiozin/issues/139)) ([64e8583](https://github.com/fdmorison/tiozin/commit/64e85833eb251f18c0a8c053e1285c4adec1ec05))
* Introduce Object Model and refine Family Model docs ([#134](https://github.com/fdmorison/tiozin/issues/134)) ([d89f94b](https://github.com/fdmorison/tiozin/commit/d89f94b7e74e45742e5c8df08823bd0d98d474ec))
* Introduce User Guides ([#140](https://github.com/fdmorison/tiozin/issues/140)) ([da91a8e](https://github.com/fdmorison/tiozin/commit/da91a8ed64e91d6c13c8729d2665d764b5283980))
* Refine user-facing documentation ([#141](https://github.com/fdmorison/tiozin/issues/141)) ([4e947ff](https://github.com/fdmorison/tiozin/commit/4e947fffd27bf100b6b8dc2654f991284d45de89))
* Reorganize navigation structure ([#167](https://github.com/fdmorison/tiozin/issues/167)) ([486b52d](https://github.com/fdmorison/tiozin/commit/486b52df6444adba4b158be6bdd3dbd9e2618b06))
* Review and improve Tiozin Family documentation ([#120](https://github.com/fdmorison/tiozin/issues/120)) ([7553634](https://github.com/fdmorison/tiozin/commit/7553634b550193774cbb5608dfad026b8060a236))
* Review tio_duckdb and tio_spark reference pages ([#146](https://github.com/fdmorison/tiozin/issues/146)) ([65d9008](https://github.com/fdmorison/tiozin/commit/65d900889280e01a1954d30d72aaa0b1a078638b))
* Revise families extending guide ([#143](https://github.com/fdmorison/tiozin/issues/143)) ([40537ee](https://github.com/fdmorison/tiozin/commit/40537ee8767654b2ba64e70962d967d8cedd4f19))
* Split tio_kernel, tio_spark, and tio_duckdb into per-component pages ([#157](https://github.com/fdmorison/tiozin/issues/157)) ([2f0e0c7](https://github.com/fdmorison/tiozin/commit/2f0e0c7a3074c00ce52241e5e7fba43e3c9b3439))


### Code Refactoring

* **core:** Adopt Tiozin and Tio naming across the codebase ([#125](https://github.com/fdmorison/tiozin/issues/125)) ([ecbee0d](https://github.com/fdmorison/tiozin/commit/ecbee0d3f0b35ce89e683731e8e99024e72fc5a7))
* **core:** Default treats only None as unset and is now recursive ([#201](https://github.com/fdmorison/tiozin/issues/201)) ([872cbf1](https://github.com/fdmorison/tiozin/commit/872cbf19814a11f510d71bde61cf58ea1b116108))
* **core:** Integrate Settings System into TiozinApp, Lifecycle, and CLI ([#151](https://github.com/fdmorison/tiozin/issues/151)) ([b3d6831](https://github.com/fdmorison/tiozin/commit/b3d68315d00f3b4665d96efc6238fae14b0c1f52))
* **core:** Redesign Context execution model to align with Python context management ([#126](https://github.com/fdmorison/tiozin/issues/126)) ([81f79c1](https://github.com/fdmorison/tiozin/commit/81f79c1744d89bb0eb4b5418d7d6cd8987ecfb87))
* **core:** Reduce DAY template aliases ([#162](https://github.com/fdmorison/tiozin/issues/162)) ([a2e8d99](https://github.com/fdmorison/tiozin/commit/a2e8d9908ad4558581d2b85d88b1076bd3cf0bdf))
* **core:** Registry contract to allow domain-specific APIs ([#199](https://github.com/fdmorison/tiozin/issues/199)) ([c473636](https://github.com/fdmorison/tiozin/commit/c4736360bbbc2b5afa9835f1cb9e0b938cd4826c))
* **core:** Rename [@self](https://github.com/self) token to [@data](https://github.com/data) ([#142](https://github.com/fdmorison/tiozin/issues/142)) ([ccc1138](https://github.com/fdmorison/tiozin/commit/ccc11387d6f68924997b726ed76ba66c30078f18))
* **core:** Rename core components ([#163](https://github.com/fdmorison/tiozin/issues/163)) ([3fc4e5f](https://github.com/fdmorison/tiozin/commit/3fc4e5f4fad53136788bbe0533296a5ed3adeae7))
* **core:** Review exception model and introduce retryable support ([#135](https://github.com/fdmorison/tiozin/issues/135)) ([b627b75](https://github.com/fdmorison/tiozin/commit/b627b754537edc4a9ec7936dcd2f0d1ea1d523b7))
* **core:** Simplify TiozinApp lifecycle ([#159](https://github.com/fdmorison/tiozin/issues/159)) ([260c8dd](https://github.com/fdmorison/tiozin/commit/260c8dd3d38e6c2769d298c2975e4f6cf228a560))

## [2.0.0](https://github.com/fdmorison/tiozin/compare/tiozin-v1.5.0...tiozin-v2.0.0) (2026-01-26)


### ⚠ BREAKING CHANGES

* unify JobContext and StepContext into single Context ([#106](https://github.com/fdmorison/tiozin/issues/106))

### Features

* unify JobContext and StepContext into single Context ([#106](https://github.com/fdmorison/tiozin/issues/106)) ([52aa652](https://github.com/fdmorison/tiozin/commit/52aa652269a46b4a15b8659c67c7efbe9bfef624))

## [1.5.0](https://github.com/fdmorison/tiozin/compare/tiozin-v1.4.0...tiozin-v1.5.0) (2026-01-25)


### Features

* **tio_spark:** Add Spark Connect, master and Hive support to SparkRunner ([#102](https://github.com/fdmorison/tiozin/issues/102)) ([c7b0f42](https://github.com/fdmorison/tiozin/commit/c7b0f42e2c447f4fd646a2b1a3a05fd40f7084ed))


### Bug Fixes

* **security:** Disable show_locals by default and cleanup CI/CD ([#105](https://github.com/fdmorison/tiozin/issues/105)) ([6a63736](https://github.com/fdmorison/tiozin/commit/6a63736bb48a3fc8ff31cf4b427e0bf81b80c81e))
* **security:** Prevent sensitive local variables from appearing in exception tracebacks ([#104](https://github.com/fdmorison/tiozin/issues/104)) ([b9bda04](https://github.com/fdmorison/tiozin/commit/b9bda040eb860df2b1715dc324e8abc9367289f0))


### Documentation

* Sanitize Changelog ([#101](https://github.com/fdmorison/tiozin/issues/101)) ([9d63c88](https://github.com/fdmorison/tiozin/commit/9d63c88983c00178c87c02132bb9b986433c95b4))

## [1.4.0](https://github.com/fdmorison/tiozin/compare/tiozin-v1.2.2...tiozin-v1.3.0) (2026-01-22)


### Features

* **tio_spark:** Add SparkIcebergRunner ([#95](https://github.com/fdmorison/tiozin/issues/95)) ([05cae74](https://github.com/fdmorison/tiozin/commit/05cae74bf844c4f6e1a4193a53d807e699b1e9ab))

## [1.2.2](https://github.com/fdmorison/tiozin/compare/tiozin-v1.2.1...tiozin-v1.2.2) (2026-01-21)


### Note

This release was generated due to early release automation issues and does not introduce any user-facing changes.

It can be safely skipped. The next meaningful release is 1.4.0.

## [1.2.1](https://github.com/fdmorison/tiozin/compare/tiozin-v1.2.0...tiozin-v1.2.1) (2026-01-21)


### Bug Fixes

* ENV merging when building template context ([#86](https://github.com/fdmorison/tiozin/issues/86)) ([6edb301](https://github.com/fdmorison/tiozin/commit/6edb301c89b716b732d59f9eed7b4c0360cdc58e))


### Note
This release also included internal CI/CD and release automation adjustments which do not affect runtime behavior.

## [1.2.0](https://github.com/fdmorison/tiozin/compare/tiozin-v1.1.0...tiozin-v1.2.0) (2026-01-20)

### Features

* Tio Spark provider with basic Runner, Inputs, Outputs, Transforms, and declarative job examples ([#81](https://github.com/fdmorison/tiozin/issues/81)) ([8312c61](https://github.com/fdmorison/tiozin/commit/8312c613c8949cfa98384ba7903fecf38d491588))

## [1.1.0](https://github.com/fdmorison/tiozin/compare/tiozin-v1.0.0...tiozin-v1.1.0) (2026-01-18)


### Features

* Add base skeletons for Tio registries with docstrings ([#2](https://github.com/fdmorison/tiozin/issues/2)) ([48ce2ac](https://github.com/fdmorison/tiozin/commit/48ce2acbc6d8550c75b9d9ee8c1d68adc22222ee))
* Add cloud storage support to FileJobRegistry via fsspec ([#54](https://github.com/fdmorison/tiozin/issues/54)) ([b383a31](https://github.com/fdmorison/tiozin/commit/b383a314de710b1c4d49bd4ffd5b1afd0553f2d7))
* Add CombineTransform for multi-dataset operations ([#34](https://github.com/fdmorison/tiozin/issues/34)) ([b29bb09](https://github.com/fdmorison/tiozin/commit/b29bb09c77194961afee15d8363a7d98cdef5d32))
* Add JobBuilder with fluent interface ([#40](https://github.com/fdmorison/tiozin/issues/40)) ([cb82818](https://github.com/fdmorison/tiozin/commit/cb82818034b3fd4be8b2871277f212da1ed69835))
* Add plugin naming and provider policies system ([#28](https://github.com/fdmorison/tiozin/issues/28)) ([8505744](https://github.com/fdmorison/tiozin/commit/8505744308a3a666d2994141badb73d89f334736))
* Add proxy composition mechanism for executable plugins ([#56](https://github.com/fdmorison/tiozin/issues/56)) ([34a7148](https://github.com/fdmorison/tiozin/commit/34a71488d8b90257f49ad5d5009e30ce9ddd1dee))
* Add PyPI classifiers and keywords for better discoverability ([#76](https://github.com/fdmorison/tiozin/issues/76)) ([62e42b4](https://github.com/fdmorison/tiozin/commit/62e42b4c25e6b491f310c112e3a1c2e511a843be))
* Add reflection and normalization helpers ([#36](https://github.com/fdmorison/tiozin/issues/36)) ([108a80c](https://github.com/fdmorison/tiozin/commit/108a80c36049035e1ea0e107bfdf648c534d439f))
* Add tuple support to plugin template overlay system ([#62](https://github.com/fdmorison/tiozin/issues/62)) ([97ec0e3](https://github.com/fdmorison/tiozin/commit/97ec0e3790ceeaee75ebc7a9310ee950c4a26bc9))
* Add utility helper functions for default values, list conversion, and UTC timestamps ([#33](https://github.com/fdmorison/tiozin/issues/33)) ([1512dc7](https://github.com/fdmorison/tiozin/commit/1512dc745815108114bd609c5df08f9f91e2ea85))
* Added PluginFactory for plugin discovery and management ([#29](https://github.com/fdmorison/tiozin/issues/29)) ([8f54b96](https://github.com/fdmorison/tiozin/commit/8f54b96fd6ef79581e64625b979f4485bcd6c491))
* Beautiful structured logging with TiozinLogger and structlog ([#45](https://github.com/fdmorison/tiozin/issues/45)) ([a3540ad](https://github.com/fdmorison/tiozin/commit/a3540adf21b05d3081a38b14a51ad1868992fa8f))
* Define pluggable Service and Resource models for Tiozin ([#13](https://github.com/fdmorison/tiozin/issues/13)) ([193dc8e](https://github.com/fdmorison/tiozin/commit/193dc8ed83b39e403fde3c3bfec68f77f30e7101))
* Enrich templates with Jinja datetime filters ([#73](https://github.com/fdmorison/tiozin/issues/73)) ([6e99a5b](https://github.com/fdmorison/tiozin/commit/6e99a5bea0bb1336323b2e6493bcb17495a72818))
* Expose environment variables to templates ([#72](https://github.com/fdmorison/tiozin/issues/72)) ([03be590](https://github.com/fdmorison/tiozin/commit/03be590e77e66a0e19495c78aab496f4bdf33d55))
* Extend helpers to support sequences and fix proxy type hints ([#60](https://github.com/fdmorison/tiozin/issues/60)) ([d16c36d](https://github.com/fdmorison/tiozin/commit/d16c36d7bee0f368b9617edee5507f45bacbe693))
* File-based job registry with JobManifest support ([#8](https://github.com/fdmorison/tiozin/issues/8)) ([d9caf53](https://github.com/fdmorison/tiozin/commit/d9caf538445acdc2091c516437215f2df8adf640))
* Improve helpers API with deep flattening and merge semantics ([#58](https://github.com/fdmorison/tiozin/issues/58)) ([2b29844](https://github.com/fdmorison/tiozin/commit/2b29844682f57c4cfac96be760fc235481b024b4))
* Introduce layered Context model with template variables and execution proxies ([#65](https://github.com/fdmorison/tiozin/issues/65)) ([8ff61b1](https://github.com/fdmorison/tiozin/commit/8ff61b12277acb4b6eded18d05815d01f6648485))
* Introduce the plugin template overlay system ([#61](https://github.com/fdmorison/tiozin/issues/61)) ([c737fbe](https://github.com/fdmorison/tiozin/commit/c737fbe01f5131bb00f765104100fd3d3e75506d))
* Introduce TioApp the central orchestrator for pipeline execution ([#5](https://github.com/fdmorison/tiozin/issues/5)) ([ed44658](https://github.com/fdmorison/tiozin/commit/ed4465828b621ae2ce3d10773d1b04ff2e37da50))
* Make Job pluggable and add LinearJob implementation ([#35](https://github.com/fdmorison/tiozin/issues/35)) ([f9263a9](https://github.com/fdmorison/tiozin/commit/f9263a997a4bac4bfee24901fdd197c5eaac351d))
* Propagate taxonomy attributes from Job to pipeline steps ([#59](https://github.com/fdmorison/tiozin/issues/59)) ([eb34a1c](https://github.com/fdmorison/tiozin/commit/eb34a1ca426bdd26f2912e3bdbe33115b0d41c6d))
* Redesign template context with support for relative dates ([#71](https://github.com/fdmorison/tiozin/issues/71)) ([c26e79e](https://github.com/fdmorison/tiozin/commit/c26e79e2b0870b9eaeddfc50d8d058e89e5ef11f))
* Skeletons for Job, JobBuilder, Resource, RegistryFactory, Logs and Context ([#4](https://github.com/fdmorison/tiozin/issues/4)) ([9cc5869](https://github.com/fdmorison/tiozin/commit/9cc5869c65351c09ebe69bebb192f20eb8f5aec3))
* Support for Local Temporary Working directories ([#70](https://github.com/fdmorison/tiozin/issues/70)) ([d57fbd5](https://github.com/fdmorison/tiozin/commit/d57fbd5e0ebbc5e986759d95f10332287d8aa839))
* Support multiple input formats in TiozinApp.run() ([#51](https://github.com/fdmorison/tiozin/issues/51)) ([de2c6c0](https://github.com/fdmorison/tiozin/commit/de2c6c0a11cbdfe215cad82b08782528a08d1110))
* Support tia_ prefixes in provider naming policy ([#67](https://github.com/fdmorison/tiozin/issues/67)) ([44feb24](https://github.com/fdmorison/tiozin/commit/44feb243de3164ee8ad0a4288bca2efd9a7de6a5))
* Tio Framework Exceptions ([#3](https://github.com/fdmorison/tiozin/issues/3)) ([6ff0413](https://github.com/fdmorison/tiozin/commit/6ff041312838546a7661892a6e95da67ac31f49f))


### Bug Fixes

* Add missing type hints to plugin components ([#14](https://github.com/fdmorison/tiozin/issues/14)) ([eec8c17](https://github.com/fdmorison/tiozin/commit/eec8c172157821917025a849745970f805e0b915))
* Add proper exception handling for domain exceptions ([#12](https://github.com/fdmorison/tiozin/issues/12)) ([6b324c0](https://github.com/fdmorison/tiozin/commit/6b324c0624092e982d8218156d3f67664e9c1a45))
* Add pyproject.toml to release workflow trigger ([#75](https://github.com/fdmorison/tiozin/issues/75)) ([93f1eef](https://github.com/fdmorison/tiozin/commit/93f1eef2b2c449a0a6e6a754e8703a901f922d74))
* Include job name in manifest validation errors ([#37](https://github.com/fdmorison/tiozin/issues/37)) ([94b0bb7](https://github.com/fdmorison/tiozin/commit/94b0bb739163c19f039dc4828e91e47dc9a74c25))
* Preserve type hints in tioproxy decorator for IDE autocomplete ([#64](https://github.com/fdmorison/tiozin/issues/64)) ([d708b77](https://github.com/fdmorison/tiozin/commit/d708b775e80c05b1407cdf3cb85b18feef600c14))
* Registry method signatures and naming ([#52](https://github.com/fdmorison/tiozin/issues/52)) ([3d3a979](https://github.com/fdmorison/tiozin/commit/3d3a9799a771e5224d394facd29a4f4a68579baa))


### Documentation

* Add ADR-0001 defining TioKernel as the default provider ([#17](https://github.com/fdmorison/tiozin/issues/17)) ([cfe2198](https://github.com/fdmorison/tiozin/commit/cfe21987b97f7384a1c3a46bca3ea4a9846d237d))
* Add Project README ([#6](https://github.com/fdmorison/tiozin/issues/6)) ([1d925ff](https://github.com/fdmorison/tiozin/commit/1d925ff491cb9a3843bd86641ba6dfdf6dd23d93))
* Add Tio Family banner for documentation ([#46](https://github.com/fdmorison/tiozin/issues/46)) ([fcfa3c7](https://github.com/fdmorison/tiozin/commit/fcfa3c747453e6887eedf79b85ffba7cec3dc66b))
* Update Family Banner ([#47](https://github.com/fdmorison/tiozin/issues/47)) ([30cdc3b](https://github.com/fdmorison/tiozin/commit/30cdc3bc042362b05cddcf9ebe00f4ac3fd2bb80))
