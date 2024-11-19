import re
import requests
import subprocess
import time
import argparse

def run_cast_command(transaction_hash, output_file, rpc_url):
    command = [
        "cast", "run", transaction_hash,
        "--rpc-url", rpc_url
    ]
    with open(output_file, "w") as file:
        subprocess.run(command, stdout=file, text=True)

def fetch_contract_name_etherscan(contract_address, api_key):
    url = "https://api.etherscan.io/api"
    params = {
        "module": "contract",
        "action": "getsourcecode",
        "address": contract_address,
        "apikey": api_key
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "1" and data["message"] == "OK":
                result = data["result"][0]
                name = result.get("ContractName", "")
                if name:
                    print(f"Contract name found in Etherscan: {name} for address {contract_address}")
                return name if name else None
        print(f"Etherscan did not return a name for address {contract_address}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from Etherscan for address {contract_address}: {e}")
        return None

def fetch_contract_name_sourcify(chain_id, contract_address):
    url = f"https://sourcify.dev/server/files/any/{chain_id}/{contract_address}"
    headers = {"accept": "application/json"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "files" in data and len(data["files"]) > 0:
                for file in data["files"]:
                    name = file.get("name", "")
                    if name.endswith(".sol"):
                        print(f"Contract name found in Sourcify: {name} for address {contract_address}")
                        return name.replace(".sol", "")
            print(f"Sourcify did not return a name for address {contract_address}")
            return None
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from Sourcify for address {contract_address}: {e}")
        return None

def fetch_contract_name(chain_id, contract_address, api_key, cache):
    if contract_address in cache:
        print(f"Cache hit for address {contract_address}: {cache[contract_address]}")
        return cache[contract_address]
    
    name = fetch_contract_name_etherscan(contract_address, api_key)
    if name:
        cache[contract_address] = name
        return name
    
    print(f"Name not found in Etherscan for address {contract_address}. Falling back to Sourcify.")
    name = fetch_contract_name_sourcify(chain_id, contract_address)
    cache[contract_address] = name or contract_address.lower()
    return cache[contract_address]

def extract_addresses_from_file(input_file):
    eth_address_regex = r"0x[a-fA-F0-9]{40}"
    with open(input_file, "r") as file:
        content = file.read()
    return set(re.findall(eth_address_regex, content))

def generate_cast_command(transaction_hash, addresses, api_key, chain_id=1):
    address_to_name = {}
    cache = {}
    for index, address in enumerate(addresses):
        print(f"Fetching name for address: {address}")
        contract_name = fetch_contract_name(chain_id, address, api_key, cache)
        address_to_name[address] = contract_name
        if index % 5 == 4:
            print("Pausing to respect Etherscan API rate limits...")
            time.sleep(1)
    labels = " \\\n  ".join(
        [f"--label {addr}:{name}" for addr, name in address_to_name.items()]
    )
    return f"cast run \\\n  {labels} \\\n  {transaction_hash} --rpc-url http://localhost:8545"

def main():
    parser = argparse.ArgumentParser(description="Generate a cast run command with labeled addresses.")
    parser.add_argument("--tx-hash", required=True, help="The transaction hash to process.")
    parser.add_argument("--api-key", required=True, help="Etherscan API key for contract name lookup.")
    args = parser.parse_args()

    rpc_url = "http://localhost:8545"
    cast_output_file = "cast_run_output.txt"
    final_command_file = "updated_cast_command.sh"

    run_cast_command(args.tx_hash, cast_output_file, rpc_url)
    addresses = extract_addresses_from_file(cast_output_file)
    print(f"Found {len(addresses)} unique Ethereum addresses.")
    updated_command = generate_cast_command(args.tx_hash, addresses, args.api_key)
    with open(final_command_file, "w") as file:
        file.write("#!/bin/bash\n")
        file.write(updated_command + "\n")
    print(f"Updated `cast run` command saved to {final_command_file}")
    print(f"Run the command using: bash {final_command_file}")

if __name__ == "__main__":
    main()