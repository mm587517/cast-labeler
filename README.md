# cast-labeler

This script generates a `cast run` command with labeled Ethereum addresses based on their contract names. It uses the Etherscan API to fetch contract names for verified contracts and falls back to Sourcify for additional coverage. To improve efficiency, it caches previously queried addresses to avoid redundant API calls.

## Features

- Fetches contract names using the Etherscan `getsourcecode` API.
- Falls back to Sourcify for contracts not verified on Etherscan.
- Respects Etherscan's rate limit of **5 calls per second**.
- Avoids redundant queries by caching address-to-name mappings.
- Generates a `cast run` command with `--label` options for all addresses.
- Outputs a ready-to-run shell script.

## Run
  ```py
      poetry run python3 cast-labeler/cast-labeler.py
  ```
