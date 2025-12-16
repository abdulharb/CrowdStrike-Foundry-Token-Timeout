# Token Lifespan Tester

This Foundry app is designed to test the execution duration and token lifespan of a Foundry Function.

## Purpose
It attempts to run a polling loop for up to **15 minutes** (approx. 890 seconds) to verify if the function can sustain execution and if the API token remains valid throughout the duration.

## Functionality
- **Function Name**: `long-poller`
- **Endpoint**: `/poll`
- **Logic**:
    1. Logs the start time.
    2. Enters a loop that sleeps for 60 seconds.
    3. Every 60 seconds, it makes a lightweight call to the CrowdStrike `Hosts` API (`query_devices_by_filter`).
    4. Logs the status of the API call.
    5. If the token expires (HTTP 401), it logs the error and exits.
    6. If it reaches 890 seconds, it exits successfully.

## Usage

### 1. Deploy the App
Use the Foundry CLI to deploy the app to your cloud environment.
```bash
foundry apps deploy
```

### 2. Invoke the Function
You can invoke the function using an HTTP client or `curl`.

```bash
# Example curl command (requires Authentication headers if called externally, 
# or use the Foundry Console / UI Extensions to trigger it)
curl -X POST <YOUR_FUNCTION_URL>/poll
```

Or trigger it via a Workflow.

## Configuration
- **Timeout**: The function timeout is configured to `900` seconds (15 minutes) in `manifest.yml`.
- **Permissions**: The app requests `devices:read` scope to perform the API polling.
