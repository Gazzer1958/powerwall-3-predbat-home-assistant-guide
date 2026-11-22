# Tesla Powerwall 3 + Predbat + Home Assistant

A practical, step-by-step implementation guide for connecting a **Tesla Powerwall 3** to **Home Assistant** and using **Predbat** to plan battery charging, discharging and export against electricity tariffs and solar forecasts.

## Start here

1. Read the [implementation guide](docs/IMPLEMENTATION_GUIDE.md).
2. Complete the compatibility checks before buying hardware or installing Home Assistant.
3. Follow the recommended implementation order in Section 4.
4. Verify each stage before proceeding to the next.
5. Keep the system in monitor/read-only mode until telemetry, tariff data, forecasts and control mappings have been checked.

## What this repository contains

- `docs/IMPLEMENTATION_GUIDE.md` — complete guide in searchable Markdown.
- `docs/Powerwall3_PredBat_Implementation_Guide.pdf` — printable guide.
- `Powerwall3_PredBat_Implementation_Guide.docx` — editable Word source.
- `configuration/` — anonymised example YAML files from the guide's appendices.
- `custom_components/tesla_fleet_tou_test/` — supplied example custom integration source and manifest.

## Important scope and safety notes

- Written specifically for Tesla Powerwall 3, Tesla Fleet, Home Assistant and Predbat. It is not a generic guide for other inverter or battery brands.
- The examples are adapted from one installation. They are not a universal plug-and-play package.
- Replace all `YOUR_...` placeholders and map every entity ID to the actual entities in your installation.
- Never publish `secrets.yaml`, API keys, passwords, OAuth tokens, private keys or personal site identifiers.
- The supplied `apps.yaml` originated in an AppDaemon-based installation. For a new Predbat app installation, use the current official Tesla Powerwall template and the app's own configuration directory; adapt the example rather than copying it unchanged.
- The custom Tesla Fleet TOU integration is user-supplied example code, not an official Tesla or Home Assistant component. Review and test it before relying on it.
- Check current official Home Assistant, Tesla Fleet and Predbat documentation because installation steps and APIs can change.
- Do not enable automatic battery control until the checks and controlled tests in the guide have passed.

## Suggested installation sequence

1. Check that your supplier's import/export tariff data can be obtained.
2. Confirm Tesla Fleet and Powerwall Gateway compatibility.
3. Install and prepare Home Assistant.
4. Install a file editor.
5. Configure Tesla Fleet and verify Powerwall entities.
6. Install and verify the custom TOU integration.
7. Configure solar forecasting and electricity rates.
8. Install Predbat using its current recommended installation route.
9. Map sensors and controls; create supporting helpers and scripts.
10. Run monitor/read-only mode, compare the plan with real data, then test control cautiously.

## Reporting problems

When asking an AI assistant or community for help, provide the exact guide version, the current configuration files (with secrets removed), relevant entity states, timestamps, logs and automation/script traces. State what you expected and what happened. Ask for diagnosis before requesting a wholesale rewrite.

## Version

- Guide source: Version 13, reviewed 22 November 2026.
- This repository is an initial publication package. Update the version and change history whenever the guide is revised.

## License and contributions

This guide is shared for educational and troubleshooting purposes. Review all configuration and code before use. If you suggest changes, describe the Home Assistant and Predbat versions and provide evidence that the change works. Do not submit secrets or personal installation identifiers.
