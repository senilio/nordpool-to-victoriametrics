import json
import os
from datetime import date, datetime, timedelta

import requests

VM_METRIC = os.getenv("VM_METRIC", "nordpool")
VM_URL = os.getenv("VM_URL")
EL_URL = os.getenv("EL_URL", "https://www.elprisetjustnu.se/api/v1/prices")
EL_ZONE = os.getenv("EL_ZONE", "SE4")


def log(text):
    now = datetime.now()
    print(f"{now} :: {text}")


def return_vm_block(timestamps: list, values: list) -> str:
    return {
        "metric": {"__name__": VM_METRIC},
        "values": values,
        "timestamps": timestamps,
    }


def make_request(date: date) -> (list, list):
    url = f"{EL_URL}/{date.strftime("%Y/%m-%d")}_{EL_ZONE}.json"
    log(f"Fetching from {url}")
    r = requests.get(url)

    if r.status_code == 200:
        log("Success.")
        timestamps, values = [], []

        for i in json.loads(r.text):
            date = i["time_start"]
            value = i["SEK_per_kWh"]

            timestamp = int(datetime.fromisoformat(date).timestamp() * 1e3)
            timestamps.append(timestamp)
            values.append(value)
    else:
        log("Error fetching data.")
        os._exit(1)

    return (timestamps, values)


def main():
    timestamps, values = make_request(date.today() + timedelta(days=1))
    vm_json_block = return_vm_block(timestamps, values)

    log("Submitting data to VM.")
    x = requests.post(VM_URL, json=vm_json_block)
    if x.status_code == 204:
        log("Data successfully submitted to VM.")
    else:
        log(f"Error submitting data to VM. Response code {x.status_code}")


if __name__ == "__main__":
    if None in [EL_ZONE, EL_URL, VM_URL, VM_METRIC]:
        log("Missing required environment vars.")
        os._exit(1)
    main()
