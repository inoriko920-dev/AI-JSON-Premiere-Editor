# STEP03 — Helper P0 diagnostic and host gate

## Development-only, safe integration

- The CEP Node context is explicitly enabled by --enable-nodejs and --mixed-context inside the manifest Resources element. Bridges publish browser globals even if the CEP runtime injects module.exports.
- Helper activation is blocked until Premiere 24.x is detected. This is only a read-only version check, not a Premiere capability certificate.
- Python must be configured explicitly through AIJSON_P0_PYTHON_EXE as an absolute Windows path ending with python.exe. No automatic download, installation, PATH search, registry mutation or shell commands.
- Script location is fixed to helper/handshake.py inside the trusted CEP extension root. Symlink escape is refused.
- Fixed child_process.execFile arguments: -I -B helper/handshake.py --probe, shell disabled, windowsHide enabled, timeout 5000 ms, output cap 8192 bytes.
- Expected protocol AIJSON_STEP03_P0, helper version 0.0.3; all operational flags remain false and unexpected capabilities are rejected.
- The handler does not import media, edit a Premiere project, render a video, or enable the assembly button.

## Evidence distinction

Static Windows/Linux CI tests simulate browser and CEP Node interactions, malformed host responses, path safety and stale subprocess callbacks. The additional Windows runner integration test starts the actual Python interpreter configured by setup-python via Node execFile to run the helper script, but **not in Premiere**.

G3 remains **BLOCKED_HOST** until an actual Windows 11 + Adobe Premiere Pro 2024 v24.x host is available to run panel docking, version detection, click helper, close/reopen, screenshot and log readback.

## Host pilot for the next test stage

1. Load this development branch as an unpacked CEP extension on a real licensed Premiere Pro 2024 installation using the supported CEP installation method. Do not change the registry silently.
2. Open the AI JSON Premiere Editor panel; click PERIKSA HOST. Confirm actual 24.x build and record version/OS/locale/CEP runtime.
3. If Python is installed and explicitly approved for this pilot, set AIJSON_P0_PYTHON_EXE in the environment inherited by Premiere. Click PERIKSA HELPER and record diagnostic status. Without Python configuration, HELPER_PYTHON_NOT_CONFIGURED is the expected safe result.
4. Test docking, narrow width, Unicode paths (only after file picker exists in STEP04), open/close/reopen and disabled assembly buttons. Capture real screenshots and logs for docs/evidence/STEP03.
5. Do not claim AC01, AC02 or G3 PASS until these real host tests pass.
