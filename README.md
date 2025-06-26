# GPG-update-checker
A tool for checking update info of Google Play Games on PC.

# Usage
## File description
All url will be found in this three json file:
  - `gpg_release_beta.json`: Release version of GPG on PC.
  - `gpg_dev-emulator_prod.json`: Stable version of GPG developer emulator.
  - `gpg_dev-emulator_dogfood.json`: Beta version of GPG developer emulator.

## How to use the downloaded file
1. Open the .crx3 file with 7-zip.
2. Find the .exe or .msi file in this package you opened, and extract that. The file name should be like `HPE-25.6.242.1-CIP.exe` or `HPE-25.6.242.1-CIP_3pdev_prod.exe`.
3. Open Command Prompt on the folder which exe file on, and then:
    - If you downloaded dev emulator (exe file name with '3pdev'), run `{exe_file_name} /o{C601E9A4-03B0-4188-843E-80058BF16EF9} /l1518 /noui` to install.
    - If you downloaded release beta, run `{exe_file_name} /o{47B07D71-505D-4665-AFD4-4972A30C6530} /l1518 /noui` to install. 
4. If you want to use without installed, you can just extract that exe file with 7-zip. Then go to `services` folder, run `Service.exe` to start.
