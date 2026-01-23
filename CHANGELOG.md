# Changelog

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

* add base skeletons for Tio registries with docstrings ([48ce2ac](https://github.com/fdmorison/tiozin/commit/48ce2acbc6d8550c75b9d9ee8c1d68adc22222ee))
* Add base skeletons for Tio registries with docstrings ([#2](https://github.com/fdmorison/tiozin/issues/2)) ([48ce2ac](https://github.com/fdmorison/tiozin/commit/48ce2acbc6d8550c75b9d9ee8c1d68adc22222ee))
* Add cloud storage support to FileJobRegistry via fsspec ([#54](https://github.com/fdmorison/tiozin/issues/54)) ([b383a31](https://github.com/fdmorison/tiozin/commit/b383a314de710b1c4d49bd4ffd5b1afd0553f2d7))
* Add CombineTransform for multi-dataset operations ([#34](https://github.com/fdmorison/tiozin/issues/34)) ([b29bb09](https://github.com/fdmorison/tiozin/commit/b29bb09c77194961afee15d8363a7d98cdef5d32))
* Add JobBuilder with fluent interface ([#40](https://github.com/fdmorison/tiozin/issues/40)) ([cb82818](https://github.com/fdmorison/tiozin/commit/cb82818034b3fd4be8b2871277f212da1ed69835))
* Add plugin naming and provider policies system ([#28](https://github.com/fdmorison/tiozin/issues/28)) ([8505744](https://github.com/fdmorison/tiozin/commit/8505744308a3a666d2994141badb73d89f334736))
* Add proxy composition mechanism for executable plugins ([#56](https://github.com/fdmorison/tiozin/issues/56)) ([34a7148](https://github.com/fdmorison/tiozin/commit/34a71488d8b90257f49ad5d5009e30ce9ddd1dee))
* add PyPI classifiers and keywords for better discoverability ([#76](https://github.com/fdmorison/tiozin/issues/76)) ([62e42b4](https://github.com/fdmorison/tiozin/commit/62e42b4c25e6b491f310c112e3a1c2e511a843be))
* Add reflection and normalization helpers ([#36](https://github.com/fdmorison/tiozin/issues/36)) ([108a80c](https://github.com/fdmorison/tiozin/commit/108a80c36049035e1ea0e107bfdf648c534d439f))
* Add Tio framework exceptions ([6ff0413](https://github.com/fdmorison/tiozin/commit/6ff041312838546a7661892a6e95da67ac31f49f))
* add tuple support to plugin template overlay system ([#62](https://github.com/fdmorison/tiozin/issues/62)) ([97ec0e3](https://github.com/fdmorison/tiozin/commit/97ec0e3790ceeaee75ebc7a9310ee950c4a26bc9))
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
* registry definition and lifecyle ([51b890c](https://github.com/fdmorison/tiozin/commit/51b890c8ec0d181e683c14b94f0570f99fe78bd7))
* Skeletons for Job, JobBuilder, Resource, RegistryFactory, Logs and Context ([#4](https://github.com/fdmorison/tiozin/issues/4)) ([9cc5869](https://github.com/fdmorison/tiozin/commit/9cc5869c65351c09ebe69bebb192f20eb8f5aec3))
* Support for Local Temporary Working directories ([#70](https://github.com/fdmorison/tiozin/issues/70)) ([d57fbd5](https://github.com/fdmorison/tiozin/commit/d57fbd5e0ebbc5e986759d95f10332287d8aa839))
* Support multiple input formats in TiozinApp.run() ([#51](https://github.com/fdmorison/tiozin/issues/51)) ([de2c6c0](https://github.com/fdmorison/tiozin/commit/de2c6c0a11cbdfe215cad82b08782528a08d1110))
* Support tia_ prefixes in provider naming policy ([#67](https://github.com/fdmorison/tiozin/issues/67)) ([44feb24](https://github.com/fdmorison/tiozin/commit/44feb243de3164ee8ad0a4288bca2efd9a7de6a5))
* Tio Framework Exceptions ([#3](https://github.com/fdmorison/tiozin/issues/3)) ([6ff0413](https://github.com/fdmorison/tiozin/commit/6ff041312838546a7661892a6e95da67ac31f49f))


### Bug Fixes

* Add missing type hints to plugin components ([#14](https://github.com/fdmorison/tiozin/issues/14)) ([eec8c17](https://github.com/fdmorison/tiozin/commit/eec8c172157821917025a849745970f805e0b915))
* Add proper exception handling for domain exceptions ([#12](https://github.com/fdmorison/tiozin/issues/12)) ([6b324c0](https://github.com/fdmorison/tiozin/commit/6b324c0624092e982d8218156d3f67664e9c1a45))
* add pyproject.toml to release workflow trigger ([#75](https://github.com/fdmorison/tiozin/issues/75)) ([93f1eef](https://github.com/fdmorison/tiozin/commit/93f1eef2b2c449a0a6e6a754e8703a901f922d74))
* Include job name in manifest validation errors ([#37](https://github.com/fdmorison/tiozin/issues/37)) ([94b0bb7](https://github.com/fdmorison/tiozin/commit/94b0bb739163c19f039dc4828e91e47dc9a74c25))
* Preserve type hints in tioproxy decorator for IDE autocomplete ([#64](https://github.com/fdmorison/tiozin/issues/64)) ([d708b77](https://github.com/fdmorison/tiozin/commit/d708b775e80c05b1407cdf3cb85b18feef600c14))
* Registry method signatures and naming ([#52](https://github.com/fdmorison/tiozin/issues/52)) ([3d3a979](https://github.com/fdmorison/tiozin/commit/3d3a9799a771e5224d394facd29a4f4a68579baa))


### Documentation

* Add ADR-0001 defining TioKernel as the default provider ([#17](https://github.com/fdmorison/tiozin/issues/17)) ([cfe2198](https://github.com/fdmorison/tiozin/commit/cfe21987b97f7384a1c3a46bca3ea4a9846d237d))
* Add Project README ([#6](https://github.com/fdmorison/tiozin/issues/6)) ([1d925ff](https://github.com/fdmorison/tiozin/commit/1d925ff491cb9a3843bd86641ba6dfdf6dd23d93))
* add Tio Family banner for documentation ([#46](https://github.com/fdmorison/tiozin/issues/46)) ([fcfa3c7](https://github.com/fdmorison/tiozin/commit/fcfa3c747453e6887eedf79b85ffba7cec3dc66b))
* tio kernel adr ([cfe2198](https://github.com/fdmorison/tiozin/commit/cfe21987b97f7384a1c3a46bca3ea4a9846d237d))
* Update Family Banner ([#47](https://github.com/fdmorison/tiozin/issues/47)) ([30cdc3b](https://github.com/fdmorison/tiozin/commit/30cdc3bc042362b05cddcf9ebe00f4ac3fd2bb80))
