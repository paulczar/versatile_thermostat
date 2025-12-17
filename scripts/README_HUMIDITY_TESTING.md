# Automated Humidity Control Testing Scripts

This directory contains automated test scripts for the Versatile Thermostat humidity control feature.

## Available Scripts

### 1. Python Script (Recommended)

**File**: `test_humidity_control.py`

A comprehensive Python script that runs all test scenarios, verifies results, and logs detailed test results to a JSON file.

#### Features

- ✅ Automated test execution
- ✅ Detailed result logging to JSON file
- ✅ State verification with timeouts
- ✅ Comprehensive error handling
- ✅ Test summary with pass/fail statistics
- ✅ **Cycle time aware**: Automatically reads thermostat cycle time and waits appropriately to prevent short cycling

#### Prerequisites

1. Install Python dependencies:
   ```bash
   pip install homeassistant-api
   ```

2. Get a Home Assistant Long-Lived Access Token:
   - Go to Home Assistant → Profile → Long-Lived Access Tokens
   - Create a new token
   - Save it securely

3. Set environment variables (or use command-line arguments):
   ```bash
   export HASS_URL="http://localhost:8123"  # or your HA URL
   export HASS_TOKEN="your_long_lived_access_token"
   ```

#### Configuration

Edit the `DEFAULT_CONFIG` dictionary in the script:

```python
DEFAULT_CONFIG = {
    "thermostat_entity": "climate.your_thermostat",  # Your thermostat entity
    "humidity_sensor": "input_number.test_humidity",  # Your humidity sensor (see Prerequisites section)
    "humidity_threshold": 60.0,  # Your threshold
    "wait_time": None,  # Auto-calculated from cycle_min (1.5x cycle time)
    "cycle_multiplier": 1.5,  # Wait 1.5x cycle time to avoid short cycling
    "max_wait_time": None,  # Auto-calculated from cycle_min (3x cycle time)
    "log_file": "humidity_test_results.log",  # Output file
}
```

**Note**: For `humidity_sensor`, you can use:
- `input_number.test_humidity` - A test helper (create in `configuration.yaml`, see Prerequisites)
- Any real humidity sensor entity ID (e.g., `sensor.living_room_humidity`)

**Important**: The script automatically reads the thermostat's `cycle_min` configuration and calculates appropriate wait times:
- **wait_time**: Defaults to `cycle_min * 60 * 1.5` seconds (1.5 cycles)
- **max_wait_time**: Defaults to `cycle_min * 60 * 3` seconds (3 cycles)

This prevents short cycling of your HVAC equipment. For example:
- If `cycle_min = 5` minutes: `wait_time = 450` seconds (7.5 minutes), `max_wait_time = 900` seconds (15 minutes)
- If `cycle_min = 10` minutes: `wait_time = 900` seconds (15 minutes), `max_wait_time = 1800` seconds (30 minutes)

You can override these by setting `wait_time` and `max_wait_time` explicitly, but it's recommended to let the script calculate them automatically.

#### Usage

```bash
# Basic usage (uses environment variables)
python3 scripts/test_humidity_control.py

# With command-line arguments
python3 scripts/test_humidity_control.py \
  --url http://localhost:8123 \
  --token your_token \
  --thermostat climate.living_room_ac \
  --humidity-sensor input_number.test_humidity \
  --log-file my_test_results.log
```

#### Output

The script generates a JSON log file with:
- Test start/end times
- Duration
- Pass/fail statistics
- Detailed results for each test step
- Error messages and details

Example output:
```json
{
  "test_start": "2024-01-15T10:00:00",
  "test_end": "2024-01-15T10:15:00",
  "duration_seconds": 900,
  "total_tests": 15,
  "passed": 14,
  "failed": 1,
  "pass_rate": "93.3%",
  "results": [...]
}
```

### 2. YAML Script (Simple)

**File**: `humidity_test_automation.yaml`

A Home Assistant script that can be added directly to your configuration or created in the UI.

#### Features

- ✅ Simple YAML format
- ✅ Runs directly in Home Assistant
- ✅ No external dependencies
- ✅ **Cycle time aware**: Automatically reads thermostat cycle time and waits appropriately
- ⚠️ Limited error handling and logging

#### Setup

1. **Option A: Add to configuration.yaml**
   ```yaml
   # Copy contents of humidity_test_automation.yaml
   # Update entity IDs in the script
   # Wait times are automatically calculated from thermostat cycle_min
   ```

2. **Option B: Create in UI**
   - Go to Settings → Automations & Scenes → Scripts
   - Create new script
   - Copy YAML content
   - Update entity IDs

**Cycle Time Handling**: The script automatically reads `cycle_min` from your thermostat's configuration and calculates wait times:
- `wait_seconds = cycle_min * 60 * 1.5` (1.5 cycles)
- `max_wait_seconds = cycle_min * 60 * 3` (3 cycles)

This ensures the script waits long enough between state changes to prevent short cycling your HVAC equipment.

#### Usage

Call the script from Developer Tools → Services:
```yaml
service: script.humidity_control_test
```

Or trigger from an automation:
```yaml
automation:
  - alias: "Run Humidity Tests Daily"
    trigger:
      - platform: time
        at: "02:00:00"
    action:
      - service: script.humidity_control_test
```

## Test Scenarios

Both scripts test the following scenarios:

1. **Scenario 1**: DRY Mode Activation
   - Humidity high + temperature at target → DRY mode activates

2. **Scenario 2**: COOL Mode Priority
   - Cooling needed → COOL mode takes priority over DRY

3. **Scenario 3**: DRY Mode Deactivation
   - Humidity drops below threshold → DRY mode deactivates

4. **Scenario 4**: Temperature Threshold
   - Tests 0.1°C temperature threshold boundary

5. **Scenario 5**: Non-COOL Mode Ignored
   - HEAT mode not affected by humidity control

## Prerequisites for Testing

Before running tests, ensure:

1. ✅ **Thermostat configured**:
   - Type: `over_climate`
   - AC mode enabled
   - Humidity feature enabled
   - Humidity sensor configured

2. ✅ **DRY mode available**:
   - Underlying AC device supports DRY mode
   - DRY mode appears in `hvac_modes` attribute

3. ✅ **Humidity sensor** - You have two options:

   **Option A: Use `input_number` helper (Recommended for testing)**

   Create a test humidity sensor by adding this to your `configuration.yaml`:
   ```yaml
   input_number:
     test_humidity:
       name: Test Humidity Sensor
       min: 0
       max: 100
       step: 0.1
       unit_of_measurement: "%"
       initial: 55
   ```

   Then restart Home Assistant. The entity will be available as `input_number.test_humidity`.

   **⚠️ Important**: You must configure your thermostat to use this sensor:
   1. Go to **Settings → Devices & Services → Versatile Thermostat**
   2. Edit your thermostat
   3. Go to **Humidity management** step
   4. Select `input_number.test_humidity` as the humidity sensor
   5. Save the configuration

   This allows the test scripts to change the humidity value during testing. After testing, you can switch back to your real humidity sensor.

   **Option B: Use a real humidity sensor**

   ⚠️ **Note**: Real sensors are read-only, so test scripts cannot change their values. This means automated tests won't work properly with real sensors. Use Option A for testing.

   If you want to use a real sensor for manual testing only:
   - Find your humidity sensor entity ID (e.g., `sensor.living_room_humidity`)
   - Configure the thermostat to use it
   - The test scripts can read values but cannot simulate different humidity levels

   To find your humidity sensors:
   1. Go to **Developer Tools → States**
   2. Search for entities containing "humidity" or "hum"
   3. Look for sensors with `unit_of_measurement: "%"` or `%` in the name

   **For the test scripts**, use:
   - Python script: `--humidity-sensor input_number.test_humidity` (recommended)
   - YAML script: Update the `humidity_sensor` variable to `input_number.test_humidity`

4. ✅ **Access**:
   - Home Assistant API access (for Python script)
   - Long-lived access token (for Python script)

## Debug Logging

To troubleshoot test failures and see detailed information about humidity control behavior, enable debug logging for Versatile Thermostat.

### Enable Debug Logging

Add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.versatile_thermostat: debug
    custom_components.versatile_thermostat.feature_humidity_manager: debug
    custom_components.versatile_thermostat.state_manager: debug
    custom_components.versatile_thermostat.base_thermostat: debug
```

**Or** enable via the UI:
1. Go to **Settings → System → Logs**
2. Click the **⋮** menu (three dots) → **Download Full Logs**
3. Or use **Settings → System → Logs** → **Configure** to add logger configuration

### What to Look For

When debug logging is enabled, you'll see messages like:

```
INFO - HumidityManager-YourThermostat - Humidity changed from 55.0% to 65.0%
INFO - HumidityManager-YourThermostat - Humidity too high (65.0% > 60.0%), temperature at target (22.0°C), switching to DRY mode
INFO - HumidityManager-YourThermostat - Humidity too high (65.0% > 60.0%), but cooling is still needed (temp 22.5°C > target 20.0°C), keeping COOL mode
DEBUG - StateManager - Calculating HVAC mode with humidity control
DEBUG - BaseThermostat - Refreshing humidity state
```

### Viewing Logs

- **Home Assistant UI**: Settings → System → Logs
- **Log file**: Check your Home Assistant log file (location depends on installation type)
- **Python script**: Logs are also written to the console during test execution

### Disable Debug Logging

After testing, you can disable debug logging to reduce log volume:

```yaml
logger:
  default: info
  logs:
    custom_components.versatile_thermostat: info
```

Or remove the logger configuration entirely to use default logging levels.

## Troubleshooting

### Python Script Issues

**"homeassistant_api not installed"**
```bash
pip install homeassistant-api
```

**"Authentication failed"**
- Verify your access token is correct
- Check token hasn't expired
- Ensure token has appropriate permissions

**"Cannot connect to Home Assistant"**
- Verify Home Assistant URL is correct
- Check if Home Assistant is running
- Verify network connectivity

**"Entity not found"**
- Check entity IDs match your setup
- Verify entities exist in Home Assistant
- Check entity IDs are correct (case-sensitive)

### YAML Script Issues

**"Template error"**
- Verify entity IDs are correct
- Check entities exist and are accessible
- Ensure proper YAML indentation

**"Service not found"**
- Verify script is loaded in Home Assistant
- Check script name matches
- Restart Home Assistant if needed

### Test Failures

**DRY mode not activating**:
- Verify humidity > threshold
- Check temperature is at target (within 0.1°C)
- Ensure DRY mode is available
- **Enable debug logging** (see Debug Logging section above) to see detailed decision-making
- Check logs for error messages and humidity manager state

**COOL mode not overriding**:
- Verify temperature difference > 0.1°C
- Check temperature sensor is updating
- **Enable debug logging** (see Debug Logging section above) to see state manager calculations
- Review state manager logs for temperature comparison details

**State changes not happening**:
- Check thermostat `cycle_min` configuration (default: 5 minutes)
- Script automatically waits 1.5x cycle time between changes
- If your cycle time is very long (e.g., 30+ minutes), tests will take longer
- Verify no other features interfering (window detection, safety, etc.)
- Check that `max_wait_time` is sufficient (default: 3x cycle time)
- **Enable debug logging** (see Debug Logging section above) to see detailed state change information

**Short cycling concerns**:
- ✅ Script automatically prevents short cycling by reading `cycle_min`
- ✅ Wait times are calculated as 1.5x cycle time (e.g., 7.5 min for 5 min cycle)
- ✅ This ensures at least one full cycle completes before next state change
- ⚠️ If you manually override `wait_time`, ensure it's >= `cycle_min * 60` seconds

## Integration with CI/CD

The Python script can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Humidity Control Tests
  env:
    HASS_URL: ${{ secrets.HASS_URL }}
    HASS_TOKEN: ${{ secrets.HASS_TOKEN }}
  run: |
    pip install homeassistant-api
    python3 scripts/test_humidity_control.py \
      --thermostat ${{ secrets.TEST_THERMOSTAT }} \
      --humidity-sensor ${{ secrets.TEST_HUMIDITY_SENSOR }} \
      --log-file test_results.json
```

## Manual Testing

For manual testing instructions, see:
- `TESTING_HUMIDITY_REAL_WORLD.md` - Detailed manual test scenarios
- `TESTING_HUMIDITY.md` - General testing documentation

## Contributing

When adding new test scenarios:

1. Add test method to `HumidityTestRunner` class
2. Call from `run_all_tests()` method
3. Update this README with scenario description
4. Update YAML script if needed

## Support

For issues or questions:
- Check Home Assistant logs
- Review test log files
- Verify configuration
- See troubleshooting section above
