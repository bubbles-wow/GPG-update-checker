from math import log
import os
import json
import logging
import urllib3
import uuid
import packaging.version
from requests import Session

# disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s] %(message)s')

# base variables
cur_path = os.path.dirname(os.path.abspath(__file__))
session = Session()
session.verify = False
api = "https://update.googleapis.com/service/update2/json"
body = {
    "request": {
        "@os": "win",
        "@updater": "updater",
        "acceptformat": "crx3,download,puff,run,xz,zucc",
        "apps": [
            {
                "ap": "",
                "appid": "",
                "enabled": True,
                "installdate": -1,
                "installsource": "taggedmi",
                "ping": {
                    "rd": -1
                },
                "updatecheck": {
                    "sameversionupdate": True
                },
                "version": "0.0.0.0"
            }
        ],
        "arch": "x86",
        "dedup": "cr",
        "domainjoined": False,
        "hw": {
            "avx": True,
            "physmemory": 31,
            "sse": True,
            "sse2": True,
            "sse3": True,
            "sse41": True,
            "sse42": True,
            "ssse3": True
        },
        "ismachine": True,
        "nacl_arch": "x86-64",
        "os": {
            "arch": "x86_64",
            "platform": "Windows",
            "version": "10.0.26100.1"
        },
        "prodversion": "138.0.7194.0",
        "protocol": "4.0",
        "requestid": "",
        "sessionid": "",
        "updaterversion": "138.0.7194.0",
        "wow64": True
    }
}
config_list = [
    {
        "display": "GPG Official Release",
        "local": "gpg_release_beta.json",
        "ap": "beta",
        "appid": "{47B07D71-505D-4665-AFD4-4972A30C6530}"
    },
    {
        "display": "GPG Emulator Stable",
        "local": "gpg_dev-emulator_prod.json",
        "ap": "prod",
        "appid": "{c601e9a4-03b0-4188-843e-80058bf16ef9}"
    },
    {
        "display": "GPG Emulator Beta",
        "local": "gpg_dev-emulator_dogfood.json",
        "ap": "dogfood",
        "appid": "{c601e9a4-03b0-4188-843e-80058bf16ef9}"
    }
]

def version_checker(ap: str, appid: str):
    # prepare
    global body
    body["request"]["apps"][0]["ap"] = ap
    body["request"]["apps"][0]["appid"] = appid
    body["request"]["requestid"] = f"{uuid.uuid4()}"
    body["request"]["sessionid"] = f"{uuid.uuid4()}"
    # request
    res = session.post(api, json=body, timeout=10)
    if res.status_code != 200:
        raise Exception(f"Request failed with status code {res.status_code}.")

    result = res.text.replace(")]}\'\n", "")
    res_data = None
    res_data = json.loads(result)

    status = res_data["response"]["apps"][0]["updatecheck"]["status"]
    # no update
    if status == "noupdate":
        raise Exception("No update available.")
    elif status != "ok":
        raise Exception(f"Unexpected status {status}.")

    next_version = res_data["response"]["apps"][0]["updatecheck"]["nextversion"]
    url = res_data["response"]["apps"][0]["updatecheck"]["pipelines"][0]["operations"][0]["urls"][0]["url"]
    sha256 = res_data["response"]["apps"][0]["updatecheck"]["pipelines"][0]["operations"][0]["out"]["sha256"]
    path = res_data["response"]["apps"][0]["updatecheck"]["pipelines"][0]["operations"][1]["path"]
    cohort_name = res_data["response"]["apps"][0]["cohortname"]
    # print(f"Next version: {next_version}")
    # print(f"Download URL: {url}")
    # print(f"SHA256: {sha256}")
    # print(f"Path: {path}")
    result = {
        "version": next_version,
        "url": url,
        "sha256": sha256,
        "path": path,
        "cohortname": cohort_name
    }
    return result

def task(config: dict):
    display_info = config["display"]
    local_file = config["local"]
    ap = config["ap"]
    appid = config["appid"]
    try:
        # read result
        result = version_checker(ap, appid)

        # read metadata
        metadata = {}
        with open(os.path.join(cur_path, local_file), "r", encoding="utf-8") as f:
            metadata = json.load(f)
        all_channels = [item["cohortname"] for item in metadata["channels"]]

        # new channel check
        if result["cohortname"] not in all_channels:
            logging.info(f"{display_info}: New channel found: {result['cohortname']}")
            metadata["channels"].append({
                "cohortname": result["cohortname"],
                "latest": "0.0.0.0",
                "versions": {}
            })
            all_channels.append(result["cohortname"])

        channel_index = next((index for (index, d) in enumerate(metadata["channels"]) if d["cohortname"] == result["cohortname"]), None)
        if channel_index is None:
            logging.error(f"{display_info}: Channel {result['cohortname']} not found in metadata.")
            return

        latest_version = metadata["channels"][channel_index]["latest"]
        if result["version"] == latest_version or result["version"] in metadata["channels"][channel_index]["versions"]:
            logging.info(f"{display_info}: No new version found.")
            return
        
        # new version found
        logging.info(f"{display_info}: New version found: {result['version']}")
        logging.info(f"{display_info}: Cohort Name: {result['cohortname']}")
        logging.info(f"{display_info}: Download URL: {result['url']}")
        logging.info(f"{display_info}: SHA256: {result['sha256']}")
        logging.info(f"{display_info}: Path: {result['path']}")

        # update metadata
        metadata["channels"][channel_index]["latest"] = result["version"]
        metadata["channels"][channel_index]["versions"][result["version"]] = {
            "url": result["url"],
            "sha256": result["sha256"],
            "path": result["path"]
        }
        metadata["channels"][channel_index]["versions"] = dict(sorted(metadata["channels"][channel_index]["versions"].items(),
                                           key=lambda item: packaging.version.parse(item[0]), 
                                           reverse=False))
        # save to file
        with open(os.path.join(cur_path, local_file), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"{display_info}: An error occurred: {e}")
        return


if __name__ == "__main__":
    for config in config_list:
        try:
            task(config)
        except Exception as e:
            logging.error(f"An error occurred while processing {config}: {e}")
