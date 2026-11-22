
---
layout: home
title: Tesla Powerwall 3 + Predbat + Home Assistant
---

A practical, step-by-step guide to connecting a **Tesla Powerwall 3** to **Home Assistant** and using **Predbat** to plan battery charging, discharging and export.

## Start here

**[Read the complete implementation guide](docs/IMPLEMENTATION_GUIDE.md)**

Read the compatibility checks before buying hardware or installing Home Assistant. Follow the stages in order and verify each one before moving on.

## Download the guide

- [PDF guide](docs/Powerwall3_PredBat_Implementation_Guide.pdf) – convenient for reading, sharing and printing.
- [Word guide](Powerwall3_PredBat_Implementation_Guide.docx) – editable copy of the guide.
- [Complete repository ZIP](https://github.com/Gazzer1958/powerwall-3-predbat-home-assistant-guide/archive/refs/heads/main.zip) – downloads all the documentation and example files together.

## Download configuration and code examples

These are the example files used in the guide. They are also reproduced in the guide's appendices, but are available separately here for convenience.

### Home Assistant and Predbat configuration

- [apps.yaml example](configuration/apps.yaml.example) – example Predbat AppDaemon configuration. Adapt it to your installation and current Predbat installation method.
- [configuration.yaml example](configuration/configuration.yaml.example) – Home Assistant configuration examples, including relevant sensors and settings.
- [scripts.yaml example](configuration/scripts.yaml.example) – Tesla tariff-control and Powerwall operating scripts.

### Custom Tesla Fleet integration

- [Python integration – __init__.py](custom_components/tesla_fleet_tou_test/__init__.py) – custom service code used for Tesla Fleet tariff control.
- [Integration manifest – manifest.json](custom_components/tesla_fleet_tou_test/manifest.json) – integration metadata required by Home Assistant.

### Other information

- [Change history](CHANGELOG.md) – guide revisions and updates.
- [Repository README](README.md) – project scope, contents and safety notes.

## Important notes

- This guide is written specifically for Tesla Powerwall 3, Tesla Fleet, Home Assistant and Predbat. It is not a generic guide for other inverter or battery brands.
- The examples are adapted from one installation. They are not a universal plug-and-play package.
- Replace all example entity IDs, site IDs, tariff values and other installation-specific settings with your own.
- Never publish passwords, API keys, OAuth tokens, private keys or personal installation identifiers.
- The custom Tesla Fleet TOU integration is user-supplied example code, not an official Tesla or Home Assistant component. Review and test it before relying on it.
- Check current official Home Assistant, Tesla Fleet and Predbat documentation because installation methods and APIs can change.
- Do not enable automatic battery control until the checks and controlled tests in the guide have passed.

Feedback and suggestions for improvements are welcome.
