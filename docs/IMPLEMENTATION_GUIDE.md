{% raw %}

# Home Assistant, Tesla Powerwall 3 and PredBat


**Practical implementation guide — simplified, anonymised and expanded**


> This guide is based on the configuration and code supplied for the original installation. It is an adaptation starting point, not a universal plug-and-play package. Review every placeholder and installation-specific setting before enabling control.



## 1. What this guide covers


The aim of this document is to explain, in simple steps, how someone with a Tesla Powerwall 3 and Backup Gateway can minimise their monthly electricity bill by using a home automation system to control when the Powerwall charges and discharges. The system uses electricity import and export rates, predicted solar generation and predicted household consumption to decide when it is most economical to charge the battery, use stored energy or export it to the grid.

The system described in this guide uses Home Assistant, a free, open-source home automation platform, together with Predbat, an add-on for Home Assistant that analyses electricity tariffs, solar forecasts and household consumption to plan when the Powerwall should charge, discharge or export energy.

The guide explains how to connect the Powerwall to Home Assistant, provide the information Predbat needs, install and configure Predbat, and test the system safely. It includes example configuration, the relevant Home Assistant settings and scripts, and the custom Tesla Fleet integration used for the tariff-control method described here. The examples are based on one working installation, so you will need to replace installation-specific details such as entity names, tariff rates and battery settings with your own.

Predbat handles its normal planning and automatic battery control itself; you do not need to create separate Home Assistant automations for that basic operation. The guide also explains the additional scripts and integration used to apply the Powerwall tariff settings required by this particular Tesla control method.


## 2. Before you begin — using ChatGPT to assist with installation and troubleshooting


You can upload this guide to ChatGPT at the start of an installation and use it as the shared reference for the whole process. It gives ChatGPT the intended installation sequence, the purpose of the integrations, the example configuration, the script roles and the relationships between them. This should make it much easier to get step-by-step help without having to explain the whole system from scratch.

Suggested prompt: “Use the attached Powerwall 3 and Predbat implementation guide as the reference for this installation. Talk me through it one stage at a time. Before moving on, check that the current stage is working. Do not assume my entity IDs or settings match the examples; ask me to provide the relevant screenshots, YAML, logs or traces when needed. Explain any changes before asking me to make them.”

Section 2 explains how to use this guide with ChatGPT as an installation assistant. The guide supplies the background, but ChatGPT cannot see or inspect the user's Home Assistant installation unless the user shares the relevant information. The user must still provide their own entity IDs, configuration files, screenshots, logs and automation traces when requested. Remove or redact passwords, API keys, tokens and other secrets before uploading files.

- Upload the new trace/log if the result differs from the expected result.

- Test with conservative limits and observe both Home Assistant and Tesla states.

- Validate YAML/configuration before restarting or reloading.

- Change one thing at a time and record exactly what changed.

- Ask for diagnosis first; separate proven facts from possible causes.

- Capture the error and the current state before changing anything.


### A disciplined troubleshooting loop


- After receiving changed YAML, download it, open it in a text editor, check it, run Home Assistant's configuration validation where available, and make a backup before replacing the live file.

- When asking for a change, state whether you want a complete replacement file or a small patch. For a complete file, ask ChatGPT to retain all unrelated working sections.

- If a YAML file is long, upload the file rather than pasting it into the message. This avoids message truncation and preserves indentation.

- Do not paste secrets into chat. Use placeholders such as [YOUR_API_KEY] and keep real credentials in Home Assistant secrets where supported.

- Remove or replace API keys, passwords, access tokens, site IDs, public IP addresses, email addresses, phone numbers and personal notification targets before uploading.


### How to share safely


“Please analyse the attached Home Assistant/PredBat files and logs. First identify the exact failing step and explain the evidence. Do not rewrite the whole configuration yet. Check entity IDs, YAML structure, service names, units, state values and timing. Suggest the smallest low-risk diagnostic change, explain how to test it, and show exactly which file/section would change. Preserve working behaviour and flag anything that is only a hypothesis.”


### A useful troubleshooting prompt


- Expected versus actual: explain what you expected to happen, what happened instead, when it happened, and whether it worked previously.

- Entity evidence: provide the exact entity state and attributes from Developer Tools → States, plus the service/action call and response where applicable.

- Configuration files: upload the actual current apps.yaml, configuration.yaml, scripts.yaml, automations.yaml and the complete custom integration folder/files when relevant. Say which file is current and whether it is the version running now.

- Traces: for an automation or script failure, download the Home Assistant trace and upload the JSON/YAML file, or provide screenshots of the failed step and trace details.

- Logs: download or copy the relevant Home Assistant, AppDaemon/PredBat or custom integration log section. Include timestamps and several lines before and after the error, not just the final line.

- Screenshots: use the Windows Snipping Tool (or Snip & Sketch on older Windows versions) to capture the relevant Home Assistant page, error message, log entry or trace step. Save or copy the screenshot and upload it directly to ChatGPT. Include the heading, full error text, affected entity/service and surrounding context; capture more than just the final line where possible. This is often much easier than trying to describe a message or copy text from a screen.


### What to provide


ChatGPT can help inspect YAML, compare versions, interpret logs and traces, explain entity/service behaviour, and suggest a low-risk diagnostic sequence. It cannot see your Home Assistant instance unless you provide the relevant evidence, and it should not be treated as an authority to execute an untested control change.


## 3. Assumed knowledge and prerequisites



### 3.1 Check compatibility before installing


Complete these checks before buying hardware or installing Home Assistant. The first important check is how your electricity import and export rates will be supplied to Predbat. A working supplier API is useful for tariffs that change frequently, but it is not essential for every tariff: fixed and some time-of-use rates can be entered manually. Next, establish that the Tesla Powerwall 3 and the Tesla Fleet functions used by this guide are compatible. Only after these dependencies have been checked should you move on to general preparation and Home Assistant installation.


#### 3.1.1 Confirm that your electricity rates can be obtained


- An understanding of your electricity tariff: import price, export price, standing charge, time periods and the units expected by each integration.

The electricity-rate configuration in this guide has been tested with Octopus Energy. Other suppliers and rate sources may work, but their data has not been tested as part of this installation. First identify the type of tariff you use, because this determines whether you need an automated rate source.

Fixed tariff: If you pay one import rate throughout the day, a supplier API is not essential. You can enter the import rate, export rate (if applicable) and standing charge directly in Predbat's configuration.

Time-of-use tariff with known periods: If your tariff has a small number of fixed time bands, such as a cheaper overnight period and a higher daytime rate, these rates can also be entered manually in Predbat. You must enter the correct times and prices and update them if your supplier changes them.

Variable or half-hourly tariff: If prices change frequently, particularly on a half-hourly basis, an automated API or another reliable rate-data source is strongly recommended. Manually maintaining changing prices would be impractical, and Predbat needs the relevant current and future rates to plan effectively.

Predbat's rate configuration options are explained in its Energy Rates documentation. Refer to the current documentation when entering manual rates, as configuration options may change.

For tariffs that need automated rate retrieval, suppliers with potentially useful public or platform API routes to investigate include:

- EDF Energy — public residential tariff API.

- E.ON Next — API-based tariff data.

- Co-op Energy — tariff data may be available through the Octopus/Kraken platform.

- Sainsbury’s Energy — tariff data may be available through the E.ON Next platform.

- London Power — tariff data may be available through the Octopus/Kraken platform.

Useful starting points for checking published tariff data: Octopus Energy API documentation and EDF developer portal. These links are starting points only; verify that the API exposes the exact tariff and rates required.

These are potential routes to investigate, not integrations tested by this guide and not guarantees that every tariff or customer-specific rate is accessible. An API existing does not automatically mean that it exposes the customer's particular tariff, both import and export prices, or the future half-hourly prices Predbat may need. API access and endpoints can change. Some APIs provide public tariff information without authentication; others may require an account, an API key or customer-specific details.

If your tariff needs automated rates, test the rate source before buying hardware or installing Home Assistant. Tell ChatGPT your supplier, exact tariff name, region if relevant, and whether you have an export tariff. Ask it to check the supplier's current API documentation and determine how the actual rates can be retrieved. This can often be done independently of Home Assistant: a public endpoint may be checked in a browser, while an API that needs parameters or authentication can be tested with a small read-only Python script. ChatGPT can write or explain that test and help interpret the response. Do not share passwords, account tokens or API secrets in a public place.

For an automated source, check that it returns the actual import tariff and, where applicable, export tariff; half-hourly prices where required; future prices and their available horizon; and clear timestamps, time zone and units. Check that the data matches the tariff and region on your own energy account, rather than relying on a generic example or a standard tariff that you do not use. Save a sample response or test output. If the source does not expose the rates you need, consider whether the tariff can instead be entered manually or whether another source is required. For a fixed or time-of-use tariff entered manually, check the configured rates, time bands, export rate and standing charge against your supplier's latest tariff information before proceeding.


#### 3.1.2 Confirm Powerwall and Tesla Fleet compatibility


- A Tesla Powerwall 3 installation and access to the Tesla account. This guide is written for a system with a Backup Gateway. Some Tesla Fleet API functions may also work on installations without a Gateway, including access to some energy-site information and battery readings. However, Tesla's official Fleet API Energy Endpoints documentation says that its `tariff_rate` request is not available for sites without a Powerwall Gateway. In practical terms, when software asks Tesla for the site's tariff rates, Tesla rejects that request and returns an HTTP 400 error. This does not mean that the whole Tesla Fleet API is unavailable; it means that this particular tariff information cannot be retrieved using that endpoint. The tariff-reading and time-of-use tariff control method described in this guide may therefore not work without a Gateway. Compatibility has not been confirmed for those installations. Check this limitation before proceeding. Section 5.1 explains Tesla Fleet setup.


#### 3.1.3 Other preparation


- Home Assistant: if you already have a working installation, you can use it. If not, complete Section 3.2 after checking the other prerequisites. ChatGPT can guide you through choosing suitable hardware and installing Home Assistant.

- No Predbat installation is required before starting. Section 5.5 explains the current recommended Predbat installation route and how to adapt the supplied example configuration. The supplied apps.yaml is based on an earlier AppDaemon installation, so it must not be copied blindly into a different Predbat installation.

- Some familiarity with Home Assistant is helpful, but not essential. If entities, states, services, scripts, integrations or Developer Tools are unfamiliar, use the guidance in Section 2 and ask ChatGPT to explain each item before you proceed.

- A safe way to test changes, ideally when the battery is not needed for backup and with a conservative reserve level. Note that Tesla's 'Non-Backup' Powerwall configuration is still grid-connected; it simply does not provide home backup during an outage. A genuinely off-grid installation with no electricity supplier is outside the tariff-arbitrage use case covered by this guide.


### 3.2 Setting up Home Assistant


If you are starting from scratch, Home Assistant itself needs to be installed and working before you begin the Tesla and Predbat stages in Section 5. You do not need an expensive computer dedicated to this job. Home Assistant can run on a small, low-power PC that is left switched on continuously, preferably connected to your network by Ethernet.

One elegant, low-cost option is to run Home Assistant on a dedicated mini PC, such as a Lenovo ThinkCentre M710q. These are commonly found on eBay for around £70–£100. A mini PC can be left switched on continuously, uses relatively little electricity and is dedicated to Home Assistant, so it will not interfere with your normal desktop or other computer use.

The simplest arrangement is usually to install Home Assistant OS directly on the mini PC. This replaces Windows and erases the contents of the drive, so make sure there is nothing on it that you need to keep. You do not need a powerful machine for a typical Home Assistant installation.

Other options include a Raspberry Pi, Home Assistant Green, or a virtual machine on an existing computer or server. If you find a different mini PC for sale, you can paste its specification or listing into ChatGPT and ask whether it is suitable for running Home Assistant.

ChatGPT can guide you through choosing the hardware, preparing the installation media, installing Home Assistant OS, completing the first-start setup, assigning a reliable network address, updating Home Assistant and installing the File Editor or Studio Code Server add-on. Work through it one step at a time: share the screen or error you see, confirm each stage is successful, and only then move on to the next. ChatGPT cannot see or change your installation unless you share the relevant screen, files or details, and you should never upload passwords, API keys or access tokens.

Once Home Assistant is installed, updated and accessible on your network, continue with the integrations and Predbat stages in Section 5.


## 4. Recommended implementation order


- Prepare Home Assistant: install Home Assistant OS, complete initial setup, update it, configure a reliable network connection and take a full backup.

- Install a file editor: install File Editor or Studio Code Server before creating any custom integration files.

- Set up Tesla Fleet: create the Tesla Developer application, host and register the public key, complete the Home Assistant setup and confirm the Powerwall energy-site entities.

- Install the custom Tesla Fleet TOU integration: create the folder, manifest.json and __init__.py, add its configuration.yaml entry, restart Home Assistant and confirm all three actions are available.

- Set up the solar forecast: configure Solcast (or another supported source), enable half-hourly detail where applicable and verify future forecast values.

- Set up electricity prices: configure Octopus or another supported supplier source, then verify import and export rates, units, time zone and future coverage.

- Install Predbat: use the current recommended Predbat app installation for a new setup. Use the official Tesla Powerwall template as the starting point and adapt the anonymised example; do not install the retired AppDaemon method for a new system.

- Complete supporting components and mapping: create the two Text helpers, confirm the required scripts are loaded, map every sensor/control entity and check units and sign conventions.

- Run Predbat in monitor/read-only mode: wait for a complete planning cycle and compare prices, PV forecast, home load and battery SOC with their real sources.

- Test safely before enabling normal control: test the neutral tariff restore first, then the temporary charge/discharge tariff actions and operating scripts one at a time. Verify each result in Home Assistant and the Tesla app, use conservative reserve settings and restore the safe state after each test.


## 5. Add-ons and integrations: install in this order



### How the pieces fit together


Predbat is the optimiser. It does not independently know the state of your battery, tomorrow's sunshine or the price of electricity. Home Assistant integrations supply that information, and the inverter/control integration gives Predbat a way to request changes.

For a Powerwall 3 installation, think of the system as four connected layers:

- Powerwall telemetry and control — Tesla Fleet provides the cloud energy-site entities and settings used by this example.

- Solar forecast — Solcast (or another supported forecast) estimates future PV generation.

- Electricity rates — Octopus Energy or another supported source provides import and export prices.

- Predbat — combines the inputs into a plan and, once verified, controls charging/discharging through the configured control path.

Install and verify each layer separately. Do not try to troubleshoot all integrations at once.


### 5.1 Tesla Fleet — connect Home Assistant to the Powerwall 3


This is the first major integration to set up because Predbat needs accurate battery, solar, house-load and grid readings, plus a reliable way to change Powerwall settings. Tesla Fleet is the cloud API integration. It is different from Home Assistant's local Tesla Powerwall integration.


#### Before you start


- A Tesla account with a verified email address and access to the Powerwall energy site.

- A public domain with a valid HTTPS certificate. The public key must be reachable from the internet at a specific URL.

- A way to host that public key. Home Assistant's official instructions describe the NGINX Home Assistant SSL proxy or an external hosting service.

- Your Home Assistant instance and its My Home Assistant OAuth redirect integration available.


#### Step A — create a Tesla Developer application


- Open https://developer.tesla.com/request and sign in with the Tesla account associated with the energy site.

- Create an application with a recognisable name, such as Home Assistant Powerwall.

- For OAuth grant type, select Authorization Code and Machine-to-Machine.

- Set Allowed Origin URL to a public HTTPS domain that will host your Tesla public key, for example https://home.example.co.uk/. Tesla must be able to retrieve the key at https://home.example.co.uk/.well-known/appspecific/com.tesla.3p.public-key.pem. This does not have to be the address used to open the Home Assistant user interface. The key can be hosted using the NGINX Home Assistant SSL proxy or an external hosting service.

- Set Allowed Redirect URI to https://my.home-assistant.io/redirect/oauth. This is Home Assistant's standard OAuth redirect service. During authorisation, your browser returns through this service and is then directed back to your Home Assistant installation. Your browser must be able to reach Home Assistant to finish setup, but Tesla does not need direct inbound access to the Home Assistant interface.

- Select Energy Product Information — this is required for energy products. Also select Energy Product Settings so Home Assistant can change supported Powerwall settings.

- Save the application and copy its Client ID and Client Secret into a password manager. Do not put the secret in a shared YAML file or screenshot.

Tesla's developer portal changes occasionally, so use the exact field names shown there. For this Powerwall-only use case, the energy scopes are the important ones; vehicle-only scopes are not needed just to read or control the home energy site.


#### Step B — make the Tesla public key available


During Home Assistant setup, Tesla Fleet generates or requests a public key and asks for a domain on which it can be hosted. The public key file must be served at:

https://your-domain.example/.well-known/appspecific/com.tesla.3p.public-key.pem

The official Home Assistant instructions include an NGINX SSL proxy method. In outline, create the required NGINX location mapping, copy the public key into the folder served by the proxy, enable the custom NGINX configuration, restart the proxy, and test that the URL above displays the public key when opened from outside your home network. An external hosting service can be used instead.

Important: publish only the public key. Never expose the private key, Tesla Client Secret or OAuth tokens.


#### Step C — add Tesla Fleet in Home Assistant


- Go to Settings → Devices & services → Add integration.

- Search for Tesla Fleet and select it.

- Enter the Client ID and Client Secret from the developer application when requested.

- Sign in to Tesla in the browser window and approve the requested permissions.

- Return to Home Assistant, confirm the detected region, and enter the public-key domain when prompted.

- Complete the public-key registration step and wait for Home Assistant to finish creating the integration.

The virtual-key pairing step described in the Tesla Fleet documentation is for vehicle commands. It is not a step to pair the Powerwall itself. Do not confuse vehicle command signing with the energy-site setup.


#### Do I need to expose Home Assistant to the internet?


No, not necessarily. The Tesla public key must be publicly reachable over HTTPS, but the Home Assistant interface itself does not have to be publicly exposed. The browser used for the initial OAuth setup must be able to access Home Assistant when the redirect completes. Normal Tesla Fleet cloud communication does not require Tesla to initiate an inbound connection to your Home Assistant instance.

Possible remote-access arrangements:

- Home Assistant Cloud (Nabu Casa): the simplest option for remote Home Assistant access; no router port forwarding is required.

- Your own HTTPS domain: use an NGINX reverse proxy or Cloudflare Tunnel. A tunnel can avoid exposing the Home Assistant port directly.

- VPN: use Tailscale or WireGuard to reach Home Assistant privately. A VPN alone does not host the Tesla public key, so that key still needs a separate public HTTPS location.

For someone who wants to keep Home Assistant private, a VPN for administration combined with external hosting of the public key is a reasonable arrangement. Choose the method that matches the user's networking experience and security requirements.

Remote-access options: https://www.nabucasa.com/  |  https://www.cloudflare.com/products/tunnel/  |  https://tailscale.com/


#### Step D — check the entities before moving on


Open Settings → Devices & services → Tesla Fleet and confirm that the energy site/device has appeared. Then open Developer Tools → States and search for the Powerwall entities. Entity names differ between installations, so use the actual entities created on your system.

- Battery percentage / state of charge (SOC).

- Battery power (check whether positive means charging or discharging).

- Solar power and home load/consumption.

- Grid power (check whether positive means import or export).

- Operation mode, allow grid charging, allow export and backup reserve controls.

Write down the entity IDs and map them to the descriptive placeholders in the supplied apps.yaml. Some entities may be disabled by default; enable the ones needed by Predbat.

Do not enable Predbat control yet. First leave the system running and compare the sensor readings with the Tesla app and the physical behaviour of the system.


### 5.2 Install the custom Tesla Fleet TOU integration


The supplied Powerwall scripts use a small custom integration to send temporary time-of-use (TOU) tariffs to the Tesla Fleet API. Install this after the official Tesla Fleet integration is working and after you have identified your Tesla Energy Site ID. The integration reuses Tesla Fleet's existing OAuth authentication; it does not need a second Tesla application or set of credentials.


#### Step A — create the integration folder


Before this step, install and open a file editor such as Studio Code Server or File Editor (see Section 5.6). Use it to create the following folder and files.

/config/custom_components/tesla_fleet_tou_test/  
    manifest.json  
    __init__.py

The folder name must be exactly tesla_fleet_tou_test because that is the domain declared in the supplied Python source.


#### Step B — create manifest.json


Create manifest.json inside the tesla_fleet_tou_test folder and paste in this complete JSON. Save it with the exact filename manifest.json (not manifest.json.txt).

{  
  "domain": "tesla_fleet_tou_test",  
  "name": "Tesla Fleet TOU Test",  
  "version": "1.0.0",  
  "documentation": "https://www.home-assistant.io/integrations/tesla_fleet/",  
  "codeowners": [],  
  "config_flow": false,  
  "dependencies": ["tesla_fleet"],  
  "requirements": []  
}

This declares the integration domain and its dependency on the official tesla_fleet integration. The official integration must already be installed, configured and working.


#### Step C — add the Python source


Create __init__.py in the same folder. Copy the complete Python source from Appendix D into this file, from its opening module comment through the final async_setup_entry function. Do not copy only a portion of the code.


#### Step D — tell Home Assistant to load the integration


This custom integration does not provide a setup form in the Home Assistant UI. Its async_setup function registers the three services when Home Assistant loads the domain, so add the following top-level entry to /config/configuration.yaml. Do not place it inside another section, and do not add a duplicate if it is already present.

tesla_fleet_tou_test:

Save configuration.yaml and run the configuration check from Developer Tools > YAML (or the equivalent configuration check for your Home Assistant version). Correct any errors before restarting.


#### Step E — restart and verify


Restart Home Assistant fully. Reloading scripts or automations is not sufficient after adding a custom integration. After restart, check Settings > System > Logs for errors mentioning tesla_fleet_tou_test.

Open Developer Tools > Actions and search for these three actions:

tesla_fleet_tou_test.set_force_discharge_tariff  
tesla_fleet_tou_test.set_force_charge_tariff  
tesla_fleet_tou_test.restore_neutral

If the actions are missing, do not proceed with the scripts that call them. Check the folder path, exact filenames, valid JSON in manifest.json, matching domain and folder names, the configuration.yaml entry, and the official Tesla Fleet dependency. Use the first relevant Home Assistant log error to diagnose the loading failure.

No services.yaml file is required for these three actions: the Python source registers them directly with Home Assistant and defines their input schemas.


#### Step F — test the services carefully


Each action requires site_id. Use your own Tesla Energy Site ID; the code deliberately does not contain a hard-coded site identifier. The neutral-restore action applies the example baseline of 30p/kWh import and 12p/kWh export. Check the resulting tariff in the Tesla app before relying on it.


#### Optional: Home Assistant's local Tesla Powerwall integration


The built-in Tesla Powerwall integration connects locally to the Gateway and can provide additional telemetry. It supports Powerwall 3 with limitations. It is optional in this guide and is not a replacement for the Tesla Fleet settings/control entities used in the example. If you install both integrations, decide explicitly which one supplies each Predbat sensor; avoid duplicate or conflicting control paths.

Official reference: https://www.home-assistant.io/integrations/tesla_fleet and https://www.home-assistant.io/integrations/powerwall


### 5.3 Solar forecast — Solcast


If the home has solar panels, Predbat needs an estimate of how much energy they will generate in each future half-hour. The supplied configuration uses Solcast. Open-Meteo and Forecast.Solar are alternatives supported by Predbat.


#### Step A — create the Solcast forecast


- Create a Solcast account and choose the Home Assistant/PV forecast service appropriate to your account.

- Add each roof plane/array with its panel capacity, orientation (azimuth), tilt and other details requested by Solcast.

- Create or retrieve your API key. Keep it private; use Home Assistant secrets or the integration's credential field rather than publishing it in apps.yaml.

- Install the Solcast PV Forecast integration using the installation route supported by your Home Assistant release (HACS or the current Marketplace route, where available).

- In Home Assistant, add the Solcast PV Forecast integration and enter the API key and site/rooftop details.


#### Step B — enable half-hourly detail


This setting is particularly important. In the Solcast integration options, enable “forecast half-hourly detail attributes” (wording may vary slightly by version). Predbat plans in half-hour intervals. Without the detailed half-hourly attributes, the hourly forecast can be interpreted incorrectly and may overstate generation.


#### Step C — verify the forecast


- Open Developer Tools → States and search for the Solcast forecast entities.

- Open the entity attributes and confirm that forecast values are present for the coming periods, not just a single current value.

- Check that the half-hourly detailed values are present and that the daily forecast total is plausible for your array size and season.

- Confirm that the forecast refreshes automatically, or configure the supported Solcast update automation/service a few times per day. Predbat does not necessarily refresh the Solcast integration itself.

The example apps.yaml discovers Solcast entities automatically. If your entity names differ, check the Predbat solar forecast configuration and set the entity names explicitly if required.

Official reference: https://springfall2008.github.io/batpred/install/ and https://github.com/BJReplay/ha-solcast-solar


### 5.4 Electricity prices — Octopus Energy or another supplier


Predbat needs future import prices and, if you are paid for exports, export prices. These must be in the units and time intervals Predbat expects. A tariff integration is essential; Octopus is only one option.


#### Option A — Octopus Energy integration


- In Home Assistant, go to Settings → Devices & services → Add integration and search for Octopus Energy.

- Follow the login/API authentication prompts and select the electricity account, meter and tariff.

- Wait for the integration to create the current import/export rate entities and the rate-event entities.

- Open Settings → Devices & services → Octopus Energy → Entities. Enable the detailed rate/event entities for the previous day, current day and next day if they are disabled.

- In Developer Tools → States, search for octopus and inspect the current rate and event attributes.

Check import and export separately. The import sensor must match what you pay for electricity; the export sensor must match the tariff you are actually paid. Do not assume the export rate is the same as an import rate or that a sensor is enabled just because the integration is installed.


#### Octopus Agile and unpublished future prices


For Agile, actual half-hourly prices are normally available through the Octopus integration once published. Before publication, Predbat can use optional future-price estimation sources such as Nord Pool or AgilePredict, depending on the configuration. Treat these as estimates; actual supplier rates should replace them when published.


#### Option B — another supplier


If you are not with Octopus, use a supported integration or provide Predbat with correctly formatted rate sensors/values. The current Predbat energy-rates documentation describes supported sources and manual rate definitions. For manual rates, make sure the full planning horizon is covered with no missing time slots, and that import and export rates are defined independently.


#### Verify the rates before continuing


- Compare several current half-hourly rates with your supplier's app or website.

- Check that the rate units are p/kWh, not pounds/kWh, and that any conversion is handled only once.

- Confirm the timezone and start/end times align with local time and daylight-saving changes.

- Confirm future rates appear for the period Predbat plans over.

Official reference: https://springfall2008.github.io/batpred/energy-rates/


### 5.5 Install Predbat


Predbat is the optimiser that brings the data together and decides when the battery should charge, discharge or remain idle. For a new installation, the current Predbat documentation recommends the Predbat app. The older AppDaemon installation method is retired. The supplied apps.yaml and its file paths were taken from an existing AppDaemon-based installation; they are included as a worked configuration reference, not as instructions to install AppDaemon. The current Predbat app also uses an apps.yaml configuration file, but stores it in its own application directory. Follow the current installation and Tesla Powerwall inverter setup instructions for the correct template and location, then adapt the example values and scripts to your installation. Do not overwrite a new installation's template until you have backed it up.


#### Install and prepare


- Install a file editor such as Studio Code Server or File Editor. You will need it for the custom integration files, configuration and Predbat settings.

- For a new installation, follow the current Predbat app instructions: in Home Assistant, open Settings → Apps → Install app, add the official Predbat app repository (https://github.com/springfall2008/predbat_addon), refresh the list, install Predbat, enable Start on boot and start the app. If your Home Assistant version is 2026.11 or newer, use the built-in Marketplace for community projects; on 2026.10 or older, use HACS where the documentation specifies it.

- For a Tesla Powerwall, use the Tesla Fleet or Teslemetry integration supported by Predbat's Tesla Powerwall setup documentation. This guide's example uses Tesla Fleet for telemetry and settings, plus the custom TOU integration and Home Assistant scripts described in Sections 4.1–4.2. Check the current Predbat Tesla Powerwall instructions because support and configuration can change.

- Open the apps.yaml file in the Predbat app's own configuration directory. The current Predbat documentation gives the exact path shown by your installed app (the directory identifier can vary). Use the Tesla Powerwall template recommended by Predbat as the starting point, then adapt it using the supplied anonymised example in Appendix A. Do not assume the legacy AppDaemon path in Appendix A is the path for the Predbat app.

- Ensure Home Assistant Recorder retains at least 24 hours of history for the power/energy sensors Predbat needs. Do not exclude those sensors from Recorder. Predbat's current documentation recommends at least 24 hours.


#### Configure and validate


Adapt the Predbat template and the supplied example to your own entity IDs, usable battery capacity, maximum charge/discharge power, inverter sign conventions, export permissions, reserve settings, tariff source and solar forecast. The sample's 27 kWh capacity and tariff rates are installation-specific examples, not universal values. Keep the Tesla Fleet integration, custom TOU integration and Home Assistant scripts aligned with the same Powerwall site and entity IDs.

Start Predbat in monitor/read-only mode as described in the current documentation. Review the Predbat status and log. Resolve missing entities, invalid units, missing rates and forecast warnings before allowing any battery commands.

Official references: https://springfall2008.github.io/batpred/install/ and https://springfall2008.github.io/batpred/installation-summary/


### 5.6 Supporting Home Assistant components


The minimum practical setup for this Powerwall 3 example is:

- Home Assistant, with a working backup and a file editor.

- Tesla Fleet integration and the energy-site entities needed for telemetry and settings.

- A supported Powerwall inverter control path configured for Predbat.

- One solar forecast source if PV is installed.

- One import/export rate source (Octopus or another supported/manual source).

- Predbat itself and sufficient recorder history.

- Install File Editor or Studio Code Server before Section 5.2, because the custom Tesla Fleet TOU integration must be created as files under /config/custom_components/.

- Two Home Assistant Text helpers are also required by the supplied scripts: input_text.predbat_force_charge_tariff_status and input_text.predbat_force_discharge_tariff_status. Create them under Settings → Devices & services → Helpers → Create helper → Text, using those exact entity IDs (or update the scripts consistently if Home Assistant assigns different IDs).

Optional components include the local Tesla Powerwall integration for extra telemetry, HACS on Home Assistant versions that still use it for custom integrations, and visualisation cards for monitoring. EV charger integrations are only needed if you want Predbat to model EV charging.


### 5.7 Check the Powerwall measurements and control mapping


Before enabling control, compare each live Home Assistant value with the Tesla app and with the physical system. In particular, confirm the battery-power and grid-power sign conventions. A sign error can make charging appear to be discharging or grid import appear to be export.

- Confirm SOC matches the Tesla app.

- When the battery is charging, confirm the battery power sensor reports the expected sign and unit.

- When the home imports from the grid, confirm the grid power sensor reports the expected sign.

- Check solar generation and home consumption against the Tesla app or another trusted meter.

- Confirm the backup reserve and grid-charging/export controls reflect the current Tesla settings.

The supplied example was migrated incrementally from another Tesla integration. It uses a mixture of Tesla Fleet telemetry and established scripts for some Predbat control hooks. Do not assume every entity/service in that example is a direct Tesla Fleet entity; trace each configured control mapping and test it individually.


### 5.8 First start — monitor, compare, then enable control


- Start Predbat in monitor/read-only mode and wait for its first complete planning cycle.

- Check the plan's import/export prices against the supplier's rates.

- Check the PV forecast against the Solcast forecast and recent generation.

- Check predicted home load against normal household consumption.

- Check the battery SOC trajectory and reserve against the Tesla app.

- Only after the plan looks credible, test a single low-risk control operation and confirm the requested mode in Home Assistant and Tesla.

The following screenshot shows the Predbat Plan screen. It illustrates the plan information available in Predbat; the exact values and presentation may vary with configuration and version.

A successful installation should not merely show a plan. The plan should be consistent with your tariff, PV forecast, load history and actual battery behaviour. If any of those inputs look wrong, leave control disabled and troubleshoot the data source first.


### Useful official references


- Home Assistant Tesla Fleet: https://www.home-assistant.io/integrations/tesla_fleet

- Home Assistant Tesla Powerwall: https://www.home-assistant.io/integrations/powerwall

- Predbat installation: https://springfall2008.github.io/batpred/install/

- Predbat installation summary: https://springfall2008.github.io/batpred/installation-summary/

- Predbat energy rates: https://springfall2008.github.io/batpred/energy-rates/

- Solcast PV Forecast integration: https://github.com/BJReplay/ha-solcast-solar


## 6. Installation-specific values — do not copy blindly


The most important values to identify are the Tesla Energy Site ID, Home Assistant entity IDs, Solcast site/rooftop IDs, tariff sensor entities, and the usable battery capacity. Do not guess these values; retrieve them from the relevant integration or device.

Tesla Energy Site ID: open Home Assistant → Settings → Devices & services → Tesla Fleet, select the configured energy site/device and inspect its device information or integration diagnostics. The ID is also used in the Tesla Fleet API URL for the energy site. If the integration screen does not display it clearly, use the Tesla Fleet integration's diagnostics or the Tesla developer/API setup information. Use the numeric/string site identifier for the Powerwall energy site, not a vehicle VIN or Tesla account ID.

Powerwall entity IDs: open Settings → Devices & services → Tesla Fleet → the energy-site device → Entities, or open Developer Tools → States and search for terms such as percentage charged, battery power, grid power, solar power, home load, operation mode, allow charging from grid, allow export and backup reserve. Open each entity and copy its exact entity_id. The entity name shown in the guide is a placeholder; the actual prefix depends on the device name chosen during integration setup.

Solcast API key and site IDs: sign in to the Solcast account used for the PV forecast. Copy the API key from the account/API access area. The site/rooftop IDs are shown for each configured rooftop/array in the Solcast account or in the Solcast integration configuration/diagnostics. If there are multiple roof planes, list each site ID as required by the integration. Keep the API key private and store it in secrets.yaml or the integration's credential field.

Tariff sensor IDs: open Settings → Devices & services → Octopus Energy → Entities, then inspect the import/export current-rate and rate-event entities. Alternatively use Developer Tools → States and search for octopus or the supplier integration name. Confirm the units and compare the values with the supplier's app before using them in Predbat.

Battery capacity and power limits: use the Tesla app / Powerwall system details and the inverter or battery manufacturer's specifications for the installed model and expansion packs. The usable capacity is not necessarily the advertised nominal capacity. Confirm the effective value against observed SOC changes and energy charged/discharged; do not copy the sample 27 kWh figure without checking.

Entity suffixes: Home Assistant may append suffixes such as _2 or _3 when another integration has already created an entity with the same object ID. The examples in this guide assume a fresh Tesla Fleet-only setup, so the Powerwall entity placeholders do not include a suffix. If you also install Teslemetry or another integration that creates duplicate entities, Home Assistant may add a suffix; choose the Tesla Fleet entity deliberately and update every reference consistently.

Secrets and credentials: do not put API keys, passwords, access tokens or private keys directly in apps.yaml, scripts.yaml or a shared document. Use Home Assistant secrets.yaml where supported, or the integration's secure credential flow. The placeholders in the appendices are examples only.


## 7. Important operating and safety notes


- Do not assume that a successful Home Assistant service call proves the Powerwall has adopted the intended mode. Check the resulting state in Home Assistant and the Tesla app.

- Confirm the sign convention for grid, battery and inverter power. Incorrect inversion can make import look like export or charging look like discharging.

- The original configuration was an incremental migration from Teslemetry to Tesla Fleet. The supplied apps.yaml and script examples have been adapted here to illustrate the Tesla Fleet control path; verify every entity and service against the integration actually installed in your own Home Assistant.

- The safe-state example returns the system to self-consumption, disables grid charging and sets export to PV-only. Check that these are the correct safe settings for your installation and tariff.

- The automatic Predbat control scripts should retain their tariff-verification checks, safe-state handling and restoration steps. Do not remove these safeguards without understanding the consequences.

- The TOU tariff values are expressed in the units expected by this custom integration. Verify the API schema and resulting Tesla schedule before relying on them.

- A previously observed error, 'The request body is not valid', was investigated in the original work, including possible schedule-boundary/midnight issues. The supplied evidence does not establish a universal root cause; treat it as a diagnostic clue, not a definitive explanation.


## 8. Source-derived limitations and caveats


- This is an anonymised example derived from one working installation, not an official Tesla, Home Assistant or Predbat configuration. Entity names, supported controls and installation steps can change between software versions.

- The supplied apps.yaml was originally used with AppDaemon. The AppDaemon installation route for Predbat has been retired for new installations; use the current Predbat app and its own configuration directory. Treat Appendix A as a reference to adapt, not as a file to paste unchanged into every installation.

- Tesla Fleet energy-site data and settings depend on a correctly configured Tesla Developer application, public-key hosting and the permissions granted to Home Assistant. Energy Product Information is required for energy-site data and Energy Product Settings is needed for settings control. Tesla Fleet energy API calls are currently free, but Tesla's policies can change.

- The custom Tesla Fleet TOU integration in Appendix D is user-supplied example code, not an official Home Assistant or Tesla component. Review it against current Home Assistant and Tesla Fleet API behaviour, back up first, and test each action carefully before relying on it.

- The temporary tariff values, neutral tariff, battery capacity, charge/discharge limits, reserve levels, forecast settings and supplier-rate assumptions are examples from the source installation. Replace them with values appropriate to the actual system and tariff.

- Predbat support for inverter models and control methods varies. Confirm that the current Predbat Tesla Powerwall template supports the installed Powerwall and that each Home Assistant sensor, action and control responds as expected. Do not assume a successful service call means the Powerwall has completed the requested action.

- Solar forecasts, future tariff estimates and household-load predictions are not guarantees. Leave automatic control disabled until the plan has completed successfully and its inputs have been checked against actual readings.

- Battery control can affect household supply, backup reserve and grid export. Keep a conservative reserve, test one change at a time, observe the Tesla app and Home Assistant, and ensure you know how to restore the normal operating state.


## 9. Script roles and how the control flow fits together


Predbat is the planner. In the supplied apps.yaml it is configured to call four start/stop scripts when its plan requires a forced charge or discharge operation. The start scripts call the relevant tariff helper, verify that Tesla accepted the temporary tariff, and then apply the Powerwall operating settings. The stop scripts return the Powerwall to its normal operating state and restore the neutral tariff.

Why the scripts change the Powerwall tariff: the Tesla Fleet control interface used by this setup does not provide a straightforward direct “force discharge” command. Instead, the scripts temporarily change the time-of-use tariff stored in the Powerwall to make the battery behave as required: a very cheap/equalised temporary rate is used for forced charging, while a high temporary rate is used to encourage discharge/export. The scripts then apply the relevant Powerwall operating permissions and restore the normal tariff when the operation ends. These temporary control tariffs are a mechanism for influencing the Powerwall; they do not replace the real import and export prices used by Predbat to plan against the supplier tariff. Predbat continues to use its configured tariff sensors/forecast values for its cost calculations and planning.

Tariff scripts — predbat_force_charge_tariff_tesla and predbat_force_discharge_tariff_tesla call the custom Tesla Fleet TOU services to apply the temporary force-operation rates. They update a status helper so the calling script can wait for success or failure. predbat_restore_powerwall_tariff_tesla restores the normal import/export tariff after the forced operation.

Start scripts — predbat_start_force_charge_tesla waits for the force-charge tariff result before enabling grid charging and autonomous operation. If tariff verification fails, it returns the Powerwall to the safe state and stops. predbat_start_force_discharge_tesla similarly verifies the force-discharge tariff before disabling grid charging and allowing battery export. Predbat remains responsible for its own reserve/SOC planning.

Stop and safety scripts — predbat_safe_state_tesla returns the Powerwall to the configured normal operating mode (self-consumption), disables grid charging and sets export to PV-only. The stop scripts call this safety routine and then restore the neutral tariff. The force-charge start script also calls the safe-state routine if tariff verification fails.

No separate Home Assistant automation is required for Predbat's normal automatic planning and Powerwall control. Predbat calls the four start/stop scripts through apps.yaml; those scripts call the supporting tariff and safe-state helpers. Optional alert automations can be added separately, but they are not part of the required control path.

Figure 1. Relationship between Predbat's automatic start/stop scripts and their tariff and safety helpers.

Appendix D now includes installation instructions, a manifest.json for the supplied integration and the supplied __init__.py source. The manifest packages the supplied Python file as a Home Assistant custom integration; it does not replace the need to install the official Tesla Fleet integration first.


### Where Home Assistant configuration files are normally stored


On a typical Home Assistant OS installation, configuration files are stored in the /config/ folder. The main files in this guide normally belong here: configuration.yaml, automations.yaml, scripts.yaml, scenes.yaml (if used), secrets.yaml and apps.yaml (for an AppDaemon installation). Predbat's apps.yaml is normally stored in the AppDaemon configuration directory, commonly /config/appdaemon/apps/apps.yaml, rather than directly in /config/. The exact AppDaemon path depends on how AppDaemon was installed. Custom integrations are normally installed under /config/custom_components/<integration_domain>/, with the integration files (including manifest.json) inside that folder. Do not create missing files or folders solely because they appear in an example: follow the installation instructions for the specific add-on/integration. Use Home Assistant's File editor, Studio Code Server or another safe file-management method, and take a backup before editing.


### Storing API keys and other private values in secrets.yaml


Do not paste API keys, passwords or access tokens directly into configuration files that may later be shared. Home Assistant and AppDaemon both support YAML secrets, but they may use different secrets.yaml files because AppDaemon has its own configuration directory. Keep the two locations distinct and check which application loads each file.

Home Assistant secrets — normally /config/secrets.yaml:

tesla_energy_site_id: "YOUR_TESLA_ENERGY_SITE_ID"

Reference the Tesla site ID from scripts.yaml:

site_id: !secret tesla_energy_site_id

AppDaemon secrets — normally secrets.yaml in the AppDaemon configuration directory:

solcast_api_key: "YOUR_SOLCAST_API_KEY"

Reference the Solcast key from AppDaemon apps.yaml:

solcast_api_key: !secret solcast_api_key

The Tesla Energy Site ID is an identifier, not a Tesla API key. Appendix D does not require a separate API key: it reuses the OAuth credentials managed by the official Tesla Fleet integration. The calling scripts pass the site ID to the custom service.

The Solcast API key in apps.yaml is used by Predbat's AppDaemon configuration. The Solcast Home Assistant integration may also ask for credentials during its own setup; that integration's credentials are managed separately by Home Assistant.

AppDaemon normally looks for its own secrets.yaml in its configuration directory (often /config/appdaemon/), or in the location configured in appdaemon.yaml. It does not automatically mean the same file as Home Assistant's /config/secrets.yaml. See the AppDaemon documentation for its secrets setting.

Important Home Assistant limitation: using !secret in scripts.yaml prevents those YAML scripts from being viewed or edited through the Home Assistant UI script editor. They can still be loaded from YAML, but make changes in the file and reload scripts rather than editing them in the UI. Keep a backup before changing this arrangement.

Never upload secrets.yaml or unredacted credentials to ChatGPT, a forum or a public repository. If sharing scripts or apps.yaml for troubleshooting, replace secret values with placeholders.


## Appendix A — apps.yaml (complete supplied file, anonymised)


Before use, replace every YOUR_... placeholder with values from your own installation. This apps.yaml is an anonymised configuration from an earlier AppDaemon-based installation. For a new Predbat app installation, use the current Tesla Powerwall template and the app's own configuration directory, adapting this example rather than copying it unchanged.


### A1. apps.yaml


Usual location: the AppDaemon apps folder. Common paths are /config/appdaemon/apps/apps.yaml or /addon_configs/<AppDaemon add-on ID>/apps/apps.yaml. Check the AppDaemon app_dir setting in appdaemon.yaml if your installation uses a different location.


```yaml
pred_bat:
  module: predbat
  class: PredBat

  # PredBat export/force-operation control
  export_control: true
  set_export_force: true
  combine_charge_discharge: true

  # Sets the prefix for all created entities in HA
  prefix: predbat

  timezone: Europe/London

  currency_symbols:
    - '£'
    - 'p'

  threads: auto
  charge_control_immediate: false

  # ---------------------------------------------------------------------------
  # Tesla Powerwall via Tesla Fleet
  #
  # These example entity IDs assume a fresh Tesla Fleet-only installation.
  # If another integration has already created matching entities, Home Assistant
  # may append a suffix. Select the Tesla Fleet entities and update
  # the references consistently.
  # ---------------------------------------------------------------------------
  inverter_type: tesla
  inverter:
    - name: "Tesla Powerwall via Tesla Fleet"
      has_rest_api: false
      has_mqtt_api: false
      has_export_limit: false
      output_charge_control: "soc"
      has_charge_enable_time: false
      has_discharge_enable_time: false
      has_target_soc: false
      has_reserve_soc: true
      has_ge_inverter_mode: false
      charge_time_format: "S"
      charge_time_entity_is_option: false
      soc_units: "%"
      num_load_entities: 1
      time_button_press: false
      clock_time_format: "%Y-%m-%d %H:%M:%S"
      write_and_poll_sleep: 5
      has_time_window: false
      support_charge_freeze: false
      support_discharge_freeze: false
      has_idle_time: false

  inverter_charge_enable: "switch.your_energy_site_allow_charging_from_grid"
  
  inverter_reserve: "number.your_energy_site_backup_reserve"

  inverter_battery_power: sensor.your_energy_site_battery_power

  inverter_battery_power_is_negative: true
  inverter_power_factor: 1000
  tesla_force_export: true

  # ---------------------------------------------------------------------------
  # Power-flow sensors
  #
  #
  # ACTIVE CONFIGURATION:
  # These inputs now use the Tesla Fleet API entities.
  # ---------------------------------------------------------------------------

  battery_power:
    - sensor.your_energy_site_battery_power

  battery_power_invert:
    - false

  pv_power:
    - sensor.your_energy_site_solar_power

  load_power:
    - sensor.your_energy_site_load_power

  grid_power:
    - sensor.your_energy_site_grid_power

  grid_power_invert:
    - true

  inverter_reserve_max: 100

  load_today:
    - sensor.your_energy_site_home_usage

  import_today:
    - sensor.your_energy_site_grid_imported

  export_today:
    - sensor.your_energy_site_grid_exported

  pv_today:
    - sensor.your_energy_site_solar_generated

  reserve: number.your_energy_site_backup_reserve

  soc_percent:
    - sensor.your_energy_site_percentage_charged

  # Powerwall 3 + Expansion Pack nominal usable capacity
  soc_max:
    - 27

  # ---------------------------------------------------------------------------
  # Tesla Fleet charge/discharge control services
  #
  #
  #
  # Fleet migration of the PredBat telemetry and inverter control entities
  # ---------------------------------------------------------------------------
  charge_start_service:
   - service: script.predbat_start_force_charge_tesla

  charge_freeze_service:
   - service: script.predbat_stop_force_charge_tesla

  charge_stop_service:
    - service: script.predbat_stop_force_charge_tesla

  discharge_start_service:
   - service: script.predbat_start_force_discharge_tesla

  discharge_stop_service:
   - service: script.predbat_stop_force_discharge_tesla

  # ---------------------------------------------------------------------------
  # Inverter / battery power limits
  # ---------------------------------------------------------------------------
  # EXAMPLE ONLY: 11040 W. Set this to the inverter's rated power limit for your installation.
  inverter_limit: 11040
  battery_rate_max:
    # EXAMPLE ONLY: maximum battery charge/discharge power in W; check your battery/inverter specifications.
    - 11040
  battery_charge_power_curve:
    100: 1.0
  battery_discharge_power_curve:
    1: 1.0

  # EXAMPLE ONLY: set to the permitted export limit for your site, not automatically the inverter rating.
  export_limit:
    # EXAMPLE ONLY: 11040 W. Change to your DNO/agreed export limit and system configuration.
    - 11040

  # EXAMPLE VALUES BELOW ARE FOR THIS GUIDE'S PW3 + Expansion Pack setup.
  # CHANGE BOTH LIMITS to match the maximum charge/discharge rates supported by your own battery and inverter.
  # Powerwall 3 + Expansion Pack maximum charge rate is 10 kW
  inverter_limit_charge:
    # EXAMPLE ONLY: 10000 W charge limit for the PW3 + Expansion Pack configuration used in this guide.
    - 10000
  inverter_limit_discharge:
    # EXAMPLE ONLY: 11040 W discharge limit used in this guide; verify against your hardware.
    - 11040

  # ---------------------------------------------------------------------------
  # Solcast
  # ---------------------------------------------------------------------------
  solcast_host: 'https://api.solcast.com.au/'
  solcast_api_key: !secret solcast_api_key  # stored in AppDaemon's secrets.yaml
  solcast_sites:  # CHANGE: replace both example IDs with your own Solcast rooftop/site IDs
    - 'YOUR_SOLCAST_SITE_ID_1'
    - 'YOUR_SOLCAST_SITE_ID_2'
  solcast_poll_hours: 8

  pv_forecast_today: sensor.solcast_pv_forecast_forecast_today
  pv_forecast_tomorrow: sensor.solcast_pv_forecast_forecast_tomorrow
  pv_forecast_d3: sensor.solcast_pv_forecast_forecast_day_3
  pv_forecast_d4: sensor.solcast_pv_forecast_forecast_day_4

  # ---------------------------------------------------------------------------
  # Octopus tariff sensors
  # ---------------------------------------------------------------------------
  metric_octopus_import: 're:(sensor.(octopus_energy_|)electricity_[0-9a-z]+_[0-9a-z]+_current_rate)'
  metric_octopus_export: 're:(sensor.(octopus_energy_|)electricity_[0-9a-z]+_[0-9a-z]+_export_current_rate)'
  metric_standing_charge: 're:(sensor.(octopus_energy_|)electricity_[0-9a-z]+_[0-9a-z]+_current_standing_charge)'

  # ---------------------------------------------------------------------------
  # Nordpool market energy rates
  # ---------------------------------------------------------------------------
  futurerate_url: 'https://dataportal-api.nordpoolgroup.com/api/DayAheadPrices?date=DATE&market=N2EX_DayAhead&deliveryArea=UK&currency=GBP'
  futurerate_adjust_import: true
  futurerate_adjust_export: true

  # ---------------------------------------------------------------------------
  # Financial optimisation
  # ---------------------------------------------------------------------------
  calculate_day_cost: true
  include_standing_charge: false
  forward_cost_only: false

  rates_export:
    - rate: 12.0

  # Export threshold
  best_discharge_rate: 0.0

  days_previous:
    - 7
  days_previous_weight:
    - 1

  forecast_hours: 48
  forecast_plan_hours: 48
  battery_scaling: 1.0
  import_export_scaling: 1.0

  # ---------------------------------------------------------------------------
  # Export triggers
  # ---------------------------------------------------------------------------
  export_triggers:
    - name: 'large'
      minutes: 60
      energy: 1.0
    - name: 'small'
      minutes: 15
      energy: 0.25
```



## Appendix B — configuration.yaml (relevant supplied configuration)


B1 contains only the basic Home Assistant includes and the template sensor needed for the supplied Predbat configuration. Add other proxy, remote-access or notification settings separately only if your own installation requires them.


### B1. configuration.yaml


Usual location: /config/configuration.yaml (the Home Assistant configuration directory).


```yaml
# Loads default set of integrations. Do not remove.
default_config:

# Load frontend themes from the themes folder
frontend:
  themes: !include_dir_merge_named themes

automation: !include automations.yaml
script: !include scripts.yaml

template:
  - sensor:
      - name: "Template Powerwall SoC kW"
        unique_id: tesla_powerwall_soc_kwh
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: measurement
        state: >
          {% set percent = states('[YOUR_POWERWALL_SOC_SENSOR]') | float(0) %}
          {{ (percent / 100) * [YOUR_USABLE_CAPACITY_KWH] | round(2) }}
```



## Appendix C — scripts.yaml (complete retained core scripts)


The retained scripts are the core tariff, safe-state and controlled Powerwall operating functions from the supplied scripts.yaml.


### C1. scripts.yaml



```yaml
predbat_force_charge_tariff_tesla:
  alias: Predbat - Force Charge Tariff Tesla
  description: Set Powerwall tariff to 5p import / 5p export using Tesla Fleet TOU.
  mode: single
  sequence:
  - action: input_text.set_value
    target:
      entity_id: input_text.predbat_force_charge_tariff_status
    data:
      value: running
  - action: tesla_fleet_tou_test.set_force_charge_tariff
    data:
      site_id: !secret tesla_energy_site_id
  - action: input_text.set_value
    target:
      entity_id: input_text.predbat_force_charge_tariff_status
    data:
      value: success
  - action: persistent_notification.create
    data:
      title: Powerwall force-charge tariff set
      notification_id: predbat_powerwall_force_charge_tariff
      message: 'Powerwall force-charge tariff set using Tesla Fleet TOU.


        Import: £0.05/kWh

        Export: £0.05/kWh


        Tariff write completed.

        '
predbat_force_discharge_tariff_tesla:
  alias: Predbat - Force Discharge Tariff Tesla
  description: Set Powerwall tariff to 80p/80p for six hours using Tesla Fleet TOU.
  mode: single
  sequence:
  - action: tesla_fleet_tou_test.set_force_discharge_tariff
    data:
      site_id: !secret tesla_energy_site_id
  - action: persistent_notification.create
    data:
      title: Powerwall force-discharge tariff set
      notification_id: predbat_powerwall_force_discharge_tariff
      message: 'Powerwall force-discharge tariff set using Tesla Fleet TOU.


        Peak import: £0.80/kWh

        Peak export: £0.80/kWh


        Off-peak import: £0.30/kWh

        Off-peak export: £0.12/kWh


        Six-hour discharge tariff was written successfully.

        '
predbat_start_force_charge_tesla:
  alias: Predbat - Start Force Charge Tesla
  description: Set and verify the 5p/5p Tesla Fleet tariff once, then configure the Powerwall for force charge.
    PredBat remains responsible for battery reserve/SOC control.
  mode: single
  sequence:
  - action: script.predbat_force_charge_tariff_tesla
    continue_on_error: true
  - wait_template: '{{ states(''input_text.predbat_force_charge_tariff_status'') in [''success'', ''failed''] }}'
    timeout:
      seconds: 30
    continue_on_timeout: true
  - variables:
      tariff_status: '{{ states(''input_text.predbat_force_charge_tariff_status'') }}'
  - if:
    - condition: template
      value_template: '{{ tariff_status != ''success'' }}'
    then:
    - action: script.predbat_safe_state_tesla
      continue_on_error: true
    - action: persistent_notification.create
      data:
        title: PredBat force charge NOT started
        notification_id: predbat_force_charge_status
        message: '5p/5p Tesla Fleet tariff was not successfully verified.

          Tariff script status: {{ tariff_status }}

          The Powerwall has been returned to the safe normal operating controls.

          No further Powerwall parameter changes were made.

          Force charging was NOT started.

          '
    - stop: Tesla Fleet force-charge tariff was not successfully verified; force charge not started.
  - action: select.select_option
    target:
      entity_id: select.your_energy_site_operation_mode
    data:
      option: autonomous
  - action: switch.turn_on
    target:
      entity_id: switch.your_energy_site_allow_charging_from_grid
  - action: persistent_notification.create
    data:
      title: PredBat force charge started
      notification_id: predbat_force_charge_status
      message: '5p/5p Tesla Fleet tariff successfully verified.


        Powerwall configured for force charging:

        autonomous mode (Savings), grid charging enabled.


        Battery reserve/SOC remains controlled by PredBat.

        '
predbat_safe_state_tesla:
  alias: Predbat - Safe State Tesla
  description: Return the Powerwall to the normal non-forced operating state.
  mode: single
  sequence:
  - action: persistent_notification.create
    data:
      title: Predbat - Safe State - Started
      notification_id: predbat_safe_state_debug_started
      message: Safe State started. Current mode={{ states('select.your_energy_site_operation_mode') }}, grid charging={{
        states('switch.your_energy_site_allow_charging_from_grid') }}, export={{ states('select.your_energy_site_allow_export')
        }}, reserve={{ states('number.your_energy_site_backup_reserve') }}%.
  - action: persistent_notification.create
    data:
      title: Predbat - Safe State - Setting operation mode
      notification_id: predbat_safe_state_debug_mode_setting
      message: 'Requesting operation mode: self_consumption'
  - action: select.select_option
    target:
      entity_id: select.your_energy_site_operation_mode
    data:
      option: self_consumption
  - action: persistent_notification.create
    data:
      title: Predbat - Safe State - Operation mode result
      notification_id: predbat_safe_state_debug_mode_result
      message: Requested=self_consumption. Reported={{ states('select.your_energy_site_operation_mode') }}.
  - action: persistent_notification.create
    data:
      title: Predbat - Safe State - Setting grid charging
      notification_id: predbat_safe_state_debug_grid_setting
      message: 'Requesting grid charging: off'
  - action: switch.turn_off
    target:
      entity_id: switch.your_energy_site_allow_charging_from_grid
  - action: persistent_notification.create
    data:
      title: Predbat - Safe State - Grid charging result
      notification_id: predbat_safe_state_debug_grid_result
      message: Requested=off. Reported={{ states('switch.your_energy_site_allow_charging_from_grid') }}.
  - action: persistent_notification.create
    data:
      title: Predbat - Safe State - Setting export mode
      notification_id: predbat_safe_state_debug_export_setting
      message: 'Requesting export mode: pv_only'
  - action: select.select_option
    target:
      entity_id: select.your_energy_site_allow_export
    data:
      option: pv_only
  - action: persistent_notification.create
    data:
      title: Predbat - Safe State - Export mode result
      notification_id: predbat_safe_state_debug_export_result
      message: Requested=pv_only. Reported={{ states('select.your_energy_site_allow_export') }}.
  - action: persistent_notification.create
    data:
      title: Predbat - Safe State - Final values
      notification_id: predbat_safe_state_debug_final
      message: 'Final values: mode={{ states(''select.your_energy_site_operation_mode'') }}, grid charging={{ states(''switch.your_energy_site_allow_charging_from_grid'')
        }}, export={{ states(''select.your_energy_site_allow_export'') }}, reserve={{ states(''number.your_energy_site_backup_reserve'')
        }}%.'
  - action: persistent_notification.create
    data:
      title: Predbat - Safe State
      notification_id: predbat_safe_state
      message: Safe State completed successfully. Mode={{ states('select.your_energy_site_operation_mode') }}, grid
        charging={{ states('switch.your_energy_site_allow_charging_from_grid') }}, export={{ states('select.your_energy_site_allow_export')
        }}, reserve={{ states('number.your_energy_site_backup_reserve') }}%.
predbat_start_force_discharge_tesla:
  alias: Predbat - Start Force Discharge Tesla
  description: Set and verify the 80p/80p Tesla Fleet force-discharge tariff once, then configure Powerwall for
    force discharge/export. The Tesla API does not allow the sell tariff to be higher than the buy tariff, so the
    force-discharge tariff uses 80p/kWh for both import and export during the force-discharge window. This script
    does not set or monitor battery reserve/SOC; PredBat remains responsible for reserve/SOC control. Read-only
    mode and final restoration are handled by the calling coordinator.
  mode: single
  sequence:
  - action: script.predbat_force_discharge_tariff_tesla
    continue_on_error: true
  - wait_template: '{{ states(''input_text.predbat_force_discharge_tariff_status'') in [''success'', ''failed'']
      }}'
    timeout:
      seconds: 30
    continue_on_timeout: true
  - variables:
      tariff_status: '{{ states(''input_text.predbat_force_discharge_tariff_status'') }}'
  - if:
    - condition: template
      value_template: '{{ tariff_status != ''success'' }}'
    then:
    - action: script.predbat_safe_state_tesla
      continue_on_error: true
    - action: persistent_notification.create
      data:
        title: PredBat force discharge NOT started
        notification_id: predbat_force_discharge_status
        message: '80p/80p Tesla Fleet force-discharge tariff was not successfully verified.


          Tariff script status: {{ tariff_status }}


          The Powerwall has been returned to the safe normal operating controls.

          No further tariff write was attempted.


          Force discharge/export was NOT started.

          '
    - stop: Force-discharge tariff was not successfully verified; force discharge not started.
  - action: switch.turn_off
    target:
      entity_id: switch.your_energy_site_allow_charging_from_grid
  - action: select.select_option
    target:
      entity_id: select.your_energy_site_operation_mode
    data:
      option: autonomous
  - action: select.select_option
    target:
      entity_id: select.your_energy_site_allow_export
    data:
      option: battery_ok
  - action: persistent_notification.create
    data:
      title: PredBat force discharge started
      notification_id: predbat_force_discharge_status
      message: '80p/80p Tesla Fleet force-discharge tariff successfully verified.


        Powerwall configured for force discharge/export:

        autonomous mode, grid charging disabled,

        battery export enabled.


        Battery reserve/SOC is controlled by PredBat.

        '
predbat_restore_powerwall_tariff_tesla:
  alias: Predbat - Restore Powerwall Tariff Tesla
  description: Set Powerwall tariff to 30p import / 12p export using Tesla Fleet.
  mode: single
  sequence:
  - action: tesla_fleet_tou_test.restore_neutral
    data:
      site_id: !secret tesla_energy_site_id
  - action: persistent_notification.create
    data:
      title: Powerwall tariff restore requested
      notification_id: predbat_powerwall_tariff_restore
      message: 'The neutral Powerwall tariff was sent using Tesla Fleet.


        Import: £0.30/kWh

        Export: £0.12/kWh

        '
predbat_stop_force_charge_tesla:
  alias: Predbat - Stop Force Charge Tesla
  description: Return Powerwall to the safe normal state, then restore the neutral tariff using Tesla Fleet.
  mode: single
  sequence:
  - action: script.predbat_safe_state_tesla
  - action: script.predbat_restore_powerwall_tariff_tesla
  - action: persistent_notification.create
    data:
      title: PredBat force charge stopped
      notification_id: predbat_force_charge_status
      message: 'Powerwall returned to normal operation and the

        30p/12p Tesla Fleet tariff restore script was run.

        '
predbat_stop_force_discharge_tesla:
  alias: Predbat - Stop Force Discharge Tesla
  description: Stop deliberate battery export, then restore the neutral 30p/12p tariff using Tesla Fleet.
  mode: single
  sequence:
  - action: script.predbat_safe_state_tesla
  - action: script.predbat_restore_powerwall_tariff_tesla
  - action: persistent_notification.create
    data:
      title: PredBat force discharge stopped
      notification_id: predbat_force_discharge_status
      message: 'Deliberate battery export stopped.


        Powerwall returned to normal operation and the

        30p/12p Tesla Fleet tariff restore script was run.'
```



## Appendix D — custom Tesla Fleet TOU integration source


This appendix contains the complete supplied __init__.py source. Follow Section 5.2 to create the integration folder, add manifest.json, register the integration in configuration.yaml, restart Home Assistant and verify the three actions.


### D1. __init__.py — integration source


Save this file as /config/custom_components/tesla_fleet_tou_test/__init__.py. The installation procedure is in Section 5.2.


```python
"""Tesla Fleet TOU helper for Home Assistant.

This custom integration exposes three Home Assistant services which send
time-of-use (TOU) tariff definitions directly to the Tesla Fleet API:

    * set_force_discharge_tariff
    * set_force_charge_tariff
    * restore_neutral

DESIGN NOTE - SITE ID
---------------------
The Tesla Energy Site ID is deliberately NOT stored as a Python default.

Every service call must supply ``site_id`` explicitly. The Home Assistant
scripts already know which Powerwall site they are operating on, so keeping
the site ID visible at the call site avoids silently targeting a hard-coded
installation.

The service schema validates that the field exists and is non-empty before
the service callback runs. Therefore a missing site_id is rejected locally
by Home Assistant; it does not produce a request with a blank site ID.

A non-empty but incorrect site_id cannot be proven wrong locally. It is sent
to the Tesla Fleet API, which is then responsible for rejecting an unknown or
unauthorised energy site.

AUTHENTICATION
--------------
Authentication is deliberately obtained from the existing Home Assistant
Tesla Fleet config entry. This integration does not store a second set of
Tesla OAuth credentials. Home Assistant's OAuth2 session is asked to ensure
the access token is valid before each Fleet API operation.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import jwt
import voluptuous as vol
from aiohttp import ClientError

from homeassistant.components.tesla_fleet.const import (
    DOMAIN as TESLA_FLEET_DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)

REGION_SERVERS = {
    "na": "https://fleet-api.prd.na.vn.cloud.tesla.com",
    "eu": "https://fleet-api.prd.eu.vn.cloud.tesla.com",
    "cn": "https://fleet-api.prd.cn.vn.cloud.tesla.com",
}

_LOGGER = logging.getLogger(__name__)

DOMAIN = "tesla_fleet_tou_test"

SERVICE_SET_FORCE_DISCHARGE_TARIFF = "set_force_discharge_tariff"
SERVICE_SET_FORCE_CHARGE_TARIFF = "set_force_charge_tariff"
SERVICE_RESTORE_NEUTRAL = "restore_neutral"


def _validate_site_id(value: Any) -> str:
    """Validate the Tesla Energy Site ID supplied by a service call.

    ``vol.Required`` catches a completely missing site_id. This validator
    additionally rejects an empty string so that a blank value cannot make
    it into the URL sent to Tesla.

    It deliberately does not try to verify that the ID belongs to this
    user's Tesla account. That can only be established by Tesla's API.
    Therefore an incorrect but non-empty ID is still passed to Tesla and
    Tesla can reject it.

    Leading/trailing whitespace is removed so it cannot accidentally become
    part of the REST URL.
    """
    site_id = cv.string(value).strip()

    if not site_id:
        raise vol.Invalid("site_id must be a non-empty Tesla Energy Site ID.")

    return site_id


# All three services require the caller to provide the site ID explicitly.
#
# There is intentionally NO default here.
#
# Failure behaviour is therefore:
#   1. site_id omitted  -> Home Assistant rejects the service call locally.
#   2. site_id is blank -> _validate_site_id rejects it locally.
#   3. wrong non-empty ID -> the request reaches Tesla, which can reject it.
#
# This is safer than silently falling back to one hard-coded Powerwall site.
SET_SCHEMA = vol.Schema(
    {
        vol.Required("site_id"): _validate_site_id,
    }
)


FORCE_CHARGE_SCHEMA = vol.Schema(
    {
        vol.Required("site_id"): _validate_site_id,
    }
)


RESTORE_SCHEMA = vol.Schema(
    {
        vol.Required("site_id"): _validate_site_id,
    }
)


def _parse_time(value: str) -> tuple[int, int]:
    try:
        hour, minute = [int(x) for x in value.strip().split(":")]
    except (TypeError, ValueError):
        raise ServiceValidationError(
            f"Invalid time '{value}'. Use HH:MM."
        ) from None

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ServiceValidationError(
            f"Invalid time '{value}'. Use HH:MM."
        )

    return hour, minute


def _period(
    from_hour: int,
    from_minute: int,
    to_hour: int,
    to_minute: int,
) -> dict[str, int]:
    return {
        "fromDayOfWeek": 0,
        "toDayOfWeek": 6,
        "fromHour": from_hour,
        "fromMinute": from_minute,
        "toHour": to_hour,
        "toMinute": to_minute,
    }


def _build_test_periods(
    start_time: str,
    end_time: str,
) -> tuple[list[dict[str, int]], list[dict[str, int]]]:

    sh, sm = _parse_time(start_time)
    eh, em = _parse_time(end_time)

    start = sh * 60 + sm
    end = eh * 60 + em

    if start == end:
        raise ServiceValidationError(
            "Start and end time cannot be identical."
        )

    off_peak: list[dict[str, int]] = []
    on_peak: list[dict[str, int]] = []

    # Tesla Fleet represents midnight as toHour=0/toMinute=0.
    # Do not manufacture a 23:59 -> 00:00 period: the Fleet API
    # validates the complete schedule for overlaps and gaps.

    # Normal same-day window.
    if start < end:
        if start > 0:
            off_peak.append(
                _period(0, 0, sh, sm)
            )

        on_peak.append(
            _period(sh, sm, eh, em)
        )

        # End at midnight is represented by toHour=0.
        off_peak.append(
            _period(eh, em, 0, 0)
        )

    # Cross-midnight window.
    else:
        # Portion before midnight.
        on_peak.append(
            _period(sh, sm, 0, 0)
        )

        # Portion after midnight, if any.
        if end > 0:
            on_peak.append(
                _period(0, 0, eh, em)
            )

        # The remaining part of the day is off-peak.
        if end > 0:
            off_peak.append(
                _period(eh, em, sh, sm)
            )
        else:
            off_peak.append(
                _period(0, 0, sh, sm)
            )

    return off_peak, on_peak


def _build_tariff(
    *,
    name: str,
    off_peak_import: float,
    peak_import: float,
    off_peak_export: float,
    peak_export: float,
    off_peak_periods: list[dict[str, int]],
    peak_periods: list[dict[str, int]],
) -> dict[str, Any]:

    return {
        "version": 1,
        "monthly_minimum_bill": 0,
        "min_applicable_demand": 0,
        "max_applicable_demand": 0,
        "monthly_charges": 0,
        "utility": "Octopus Energy",
        "code": "OCTO-CUSTOM-FLEET-TEST",
        "name": name,
        "currency": "GBP",

        "daily_charges": [
            {
                "name": "Charge",
                "amount": 0
            }
        ],

        "daily_demand_charges": {},

        "demand_charges": {
            "ALL": {
                "rates": {
                    "ALL": 0
                }
            },
            "AllYear": {
                "rates": {}
            }
        },

        "energy_charges": {
            "ALL": {
                "rates": {
                    "ALL": 0
                }
            },
            "AllYear": {
                "rates": {
                    "OFF_PEAK": off_peak_import,
                    "ON_PEAK": peak_import
                }
            }
        },

        "seasons": {
            "AllYear": {
                "fromMonth": 1,
                "fromDay": 1,
                "toMonth": 12,
                "toDay": 31,

                "tou_periods": {
                    "OFF_PEAK": {
                        "periods": off_peak_periods
                    },
                    "ON_PEAK": {
                        "periods": peak_periods
                    }
                }
            }
        },

        "sell_tariff": {
            "min_applicable_demand": 0,
            "monthly_minimum_bill": 0,
            "monthly_charges": 0,
            "max_applicable_demand": 0,
            "utility": "Octopus Energy",

            "daily_charges": [
                {
                    "name": "Charge",
                    "amount": 0
                }
            ],

            "demand_charges": {
                "ALL": {
                    "rates": {
                        "ALL": 0
                    }
                },
                "AllYear": {
                    "rates": {}
                }
            },

            "energy_charges": {
                "ALL": {
                    "rates": {
                        "ALL": 0
                    }
                },
                "AllYear": {
                    "rates": {
                        "OFF_PEAK": off_peak_export,
                        "ON_PEAK": peak_export
                    }
                }
            },

            "seasons": {
                "AllYear": {
                    "fromMonth": 1,
                    "fromDay": 1,
                    "toMonth": 12,
                    "toDay": 31,

                    "tou_periods": {
                        "OFF_PEAK": {
                            "periods": off_peak_periods
                        },
                        "ON_PEAK": {
                            "periods": peak_periods
                        }
                    }
                }
            },

            "code": ""
        }
    }


async def _get_authenticated_fleet_session(
    hass: HomeAssistant,
) -> tuple[Any, str, str]:
    """Return the HTTP session, Fleet server and valid access token.

    The custom TOU integration deliberately reuses Home Assistant's existing
    Tesla Fleet OAuth config entry. It does not maintain a second login.

    ``async_ensure_token_valid()`` below is important because it lets the
    Home Assistant OAuth2 implementation refresh the token when necessary.
    A change to the Python site-ID handling therefore has no reason to
    trigger Tesla re-authorisation.
    """

    # Find the existing Tesla Fleet config entry. Authentication belongs to
    # the official Tesla Fleet integration, not to this custom TOU helper.
    entries = hass.config_entries.async_entries(TESLA_FLEET_DOMAIN)

    if not entries:
        raise HomeAssistantError(
            "Tesla Fleet integration is not configured."
        )

    entry: ConfigEntry = entries[0]

    implementation = (
        await async_get_config_entry_implementation(
            hass,
            entry,
        )
    )

    oauth_session = OAuth2Session(
        hass,
        entry,
        implementation,
    )

    # Ensure the access token is current before calling Tesla. This uses
    # Home Assistant's existing OAuth refresh mechanism.
    await oauth_session.async_ensure_token_valid()

    access_token = oauth_session.token[CONF_ACCESS_TOKEN]

    token = jwt.decode(
        access_token,
        options={"verify_signature": False},
    )

    region_code = token.get("ou_code")

    if not region_code:
        raise HomeAssistantError(
            "Tesla Fleet access token has no region code."
        )

    region_code = region_code.lower()

    if region_code not in REGION_SERVERS:
        raise HomeAssistantError(
            f"Unknown Tesla Fleet region: {region_code}"
        )

    session = async_get_clientsession(hass)

    return session, REGION_SERVERS[region_code], access_token


async def _send_tou(
    hass: HomeAssistant,
    site_id: str,
    tariff: dict[str, Any],
) -> None:
    """Send one complete TOU tariff to the explicitly named Tesla site.

    At this point the Home Assistant service schema has already checked that
    site_id exists and is non-empty.

    The ID is inserted into Tesla's REST path:
        /api/1/energy_sites/<site_id>/time_of_use_settings

    A valid-looking but wrong site ID is still possible. Only Tesla can
    determine whether that ID is a real energy site accessible to the
    authenticated account.
    """

    session, server, access_token = (
        await _get_authenticated_fleet_session(hass)
    )

    # Tesla identifies the target Powerwall installation through the
    # energy_sites/<site_id> part of the URL. There is deliberately no
    # fallback/default here: the validated caller-supplied ID is used.
    url = (
        f"{server}/api/1/energy_sites/"
        f"{site_id}/time_of_use_settings"
    )

    payload = {
        "tou_settings": {
            "tariff_content_v2": tariff
        }
    }

    _LOGGER.warning(
        "TESLA FLEET TOU TEST: sending tariff to site %s",
        site_id,
    )

    try:

        async with session.post(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        ) as response:

            response_text = await response.text()

            if response.status >= 400:

                _LOGGER.error(
                    "TESLA FLEET TOU TEST FAILED: HTTP %s: %s",
                    response.status,
                    response_text,
                )

                raise HomeAssistantError(
                    f"Tesla Fleet TOU request failed: "
                    f"HTTP {response.status}. "
                    f"See HA log for Tesla response."
                )

            _LOGGER.warning(
                "TESLA FLEET TOU TEST SUCCESS: "
                "Tesla returned HTTP %s",
                response.status,
            )

    except ClientError as err:

        _LOGGER.exception(
            "TESLA FLEET TOU TEST HTTP error"
        )

        raise HomeAssistantError(
            f"Tesla Fleet HTTP error: {err}"
        ) from err


async def async_setup(
    hass: HomeAssistant,
    config: dict[str, Any],
) -> bool:

    async def set_force_discharge_tariff(
        call: ServiceCall,
    ) -> None:
        """
        Set a dynamic six-hour force-discharge tariff.

        WHAT:
            Creates an ON_PEAK window with 80p import / 80p export and
            leaves the rest of the day at 30p import / 12p export.

        HOW:
            The window starts on the current 30-minute boundary and ends
            six hours later. _build_test_periods() handles normal and
            cross-midnight windows before the tariff is sent to Tesla.

        WHY:
            PredBat can temporarily make discharge/export economically
            attractive while it controls the Powerwall.

        The window starts at the current time rounded down to the
        nearest 30-minute slot and ends six hours later.

        Peak:
          Import 80p/kWh
          Export 80p/kWh

        Off-peak:
          Import 30p/kWh
          Export 12p/kWh
        """

        now = dt_util.now()

        # Round down to the latest 30-minute slot.
        start = now.replace(
            minute=(now.minute // 30) * 30,
            second=0,
            microsecond=0,
        )

        end = start + timedelta(hours=6)

        start_time = start.strftime("%H:%M")
        end_time = end.strftime("%H:%M")

        off_peak, peak = _build_test_periods(
            start_time,
            end_time,
        )

        tariff = _build_tariff(
            name=f"Force Discharge {start_time}-{end_time}",
            off_peak_import=0.30,
            peak_import=0.80,
            off_peak_export=0.12,
            peak_export=0.80,
            off_peak_periods=off_peak,
            peak_periods=peak,
        )

        _LOGGER.warning(
            "TESLA FLEET TOU: setting force discharge tariff "
            "%s to %s",
            start_time,
            end_time,
        )

        await _send_tou(
            hass,
            call.data["site_id"],
            tariff,
        )

    async def set_force_charge_tariff(
        call: ServiceCall,
    ) -> None:
        """
        Set an all-day 5p import / 5p export tariff.

        WHAT:
            Creates a full-day OFF_PEAK tariff at 5p/kWh for both import
            and export.

        HOW:
            The tariff is built locally and sent to the exact site_id
            supplied by the calling Home Assistant script.

        WHY:
            The deliberately low import price makes grid charging
            attractive during a PredBat force-charge operation.

        This is used to make grid charging attractive during
        a PredBat force-charge operation.
        """

        full_day = [
            _period(
                0,
                0,
                23,
                59,
            )
        ]

        tariff = _build_tariff(
            name="PredBat Force Charge 5p/5p",
            off_peak_import=0.05,
            peak_import=0.05,
            off_peak_export=0.05,
            peak_export=0.05,
            off_peak_periods=full_day,
            peak_periods=[],
        )

        # There is no ON_PEAK period in this tariff,
        # so remove the unused ON_PEAK rates.
        tariff["energy_charges"]["AllYear"]["rates"] = {
            "OFF_PEAK": 0.05
        }

        tariff["seasons"]["AllYear"]["tou_periods"] = {
            "OFF_PEAK": {
                "periods": full_day
            }
        }

        tariff["sell_tariff"]["energy_charges"]["AllYear"]["rates"] = {
            "OFF_PEAK": 0.05
        }

        tariff["sell_tariff"]["seasons"]["AllYear"]["tou_periods"] = {
            "OFF_PEAK": {
                "periods": full_day
            }
        }

        await _send_tou(
            hass,
            call.data["site_id"],
            tariff,
        )


    async def restore_neutral(
        call: ServiceCall,
    ) -> None:
        """Restore the known-good 30p import / 12p export neutral tariff.

        This is the normal resting tariff used after a temporary force-charge
        or force-discharge operation. The caller must explicitly provide the
        Tesla site_id, just like the two force tariff services.
        """

        # Known-good neutral tariff structure:
        # Import 30p/kWh
        # Export 12p/kWh
        #
        # One full-day OFF_PEAK period.
        #
        # IMPORTANT:
        # The OFF_PEAK period must have a matching
        # OFF_PEAK price. Do not replace this with
        # an ALL rate while leaving an OFF_PEAK period.

        full_day = [
            _period(0, 0, 23, 59),
        ]

        tariff = _build_tariff(
            name="Neutral Baseline",
            off_peak_import=0.30,
            peak_import=0.30,
            off_peak_export=0.12,
            peak_export=0.12,
            off_peak_periods=full_day,
            peak_periods=[],
        )

        # Remove the unused ON_PEAK rates because
        # the neutral tariff has no ON_PEAK period.
        tariff["energy_charges"]["AllYear"]["rates"] = {
            "OFF_PEAK": 0.30
        }

        tariff["seasons"]["AllYear"]["tou_periods"] = {
            "OFF_PEAK": {
                "periods": full_day
            }
        }

        tariff["sell_tariff"]["energy_charges"]["AllYear"]["rates"] = {
            "OFF_PEAK": 0.12
        }

        tariff["sell_tariff"]["seasons"]["AllYear"]["tou_periods"] = {
            "OFF_PEAK": {
                "periods": full_day
            }
        }

        await _send_tou(
            hass,
            call.data["site_id"],
            tariff,
        )

    # Register each service with its schema. Voluptuous validation runs
    # before the callback, so a missing/blank site_id never reaches
    # _send_tou() and cannot become a malformed Tesla URL.
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FORCE_DISCHARGE_TARIFF,
        set_force_discharge_tariff,
        schema=SET_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FORCE_CHARGE_TARIFF,
        set_force_charge_tariff,
        schema=FORCE_CHARGE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESTORE_NEUTRAL,
        restore_neutral,
        schema=RESTORE_SCHEMA,
    )

    _LOGGER.warning(
        "Tesla Fleet TOU integration loaded; site_id is required for every service call."
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Tesla Fleet TOU Test from a config entry."""

    return True
```



| Setting | What to change/check |

|---|---|

| Battery usable capacity | The example uses 27 kWh in its capacity calculation. Replace with the usable capacity of your Powerwall + expansion configuration, not the nominal figure unless that is what your sensor represents. |

| Entity IDs | All example entity IDs have been replaced with descriptive placeholders. Map each placeholder to the actual entity ID in your own Home Assistant instance. |

| Tesla Energy Site ID | Supply your own Tesla Energy Site ID to the service/script calls. Never reuse another person's site ID. |

| Solcast API key and site IDs | Insert your own credentials and site identifiers in secrets or protected configuration. Do not publish API keys in screenshots or shared files. |

| Import/export tariff values | The source examples use a 5p/5p force-charge tariff, 80p/80p force-discharge tariff and 30p import / 12p export neutral tariff. These are examples from this installation, not recommendations. Adjust to your tariff and confirm Tesla accepts the schedule. |

| Export threshold / rate assumptions | Any export rates, thresholds, multipliers or tariff periods should match your actual supplier tariff and the decision you want PredBat to make. |

| Timezone | The example uses Europe/London. Set your actual Home Assistant timezone. |

| Network/proxy settings | Use your own trusted proxy subnet and never copy the example network range without checking your topology. |

| Notification target | Replace the placeholder notify service with your own mobile or notification service. |

{% endraw %}
