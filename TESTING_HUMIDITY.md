# Testing Humidity Control Feature

This document explains how to test the humidity control feature for Versatile Thermostat.

## Testing Methods

### 1. Unit Tests (Automated)

Unit tests have been created to test the humidity feature manager and state manager integration.

#### Running Unit Tests

First, install test dependencies:
```bash
pip install -r requirements_test.txt
```

Then run the humidity-specific tests:
```bash
# Run humidity feature manager tests
pytest tests/test_humidity.py -v

# Run state manager humidity integration tests
pytest tests/test_state_manager.py::test_state_manager_humidity_control -v

# Run all tests
pytest tests/ -v
```

#### Test Coverage

The tests cover:
- ✅ Humidity manager creation and initialization
- ✅ Configuration validation (enabled/disabled, sensor presence)
- ✅ Humidity threshold checking
- ✅ Sensor state changes and refresh
- ✅ State manager integration (DRY mode switching)
- ✅ Cooling override logic (COOL mode priority)

### 2. Manual Testing in Home Assistant

#### Prerequisites

1. **AC Mode Thermostat**: The humidity feature only works with AC mode thermostats (`over_climate` type with `ac_mode` enabled)
2. **DRY Mode Support**: Your underlying AC device must support DRY mode
3. **Humidity Sensor**: A sensor that provides humidity as a percentage (0-100%)

#### Setup Steps

1. **Create/Edit a VTherm**:
   - Go to Settings → Devices & Services → Versatile Thermostat
   - Create a new thermostat or edit an existing one
   - Ensure it's an `over_climate` type with AC mode enabled

2. **Enable Humidity Feature**:
   - In the Features step, check "Use humidity management"
   - Go to the Humidity management step
   - Select your humidity sensor entity
   - Set humidity threshold (default: 60%)

3. **Verify Configuration**:
   - Check that the thermostat shows `is_humidity_configured: true` in Developer Tools → States
   - Verify `humidity_manager` attributes are present

#### Test Scenarios

##### Scenario 1: DRY Mode Activation
**Goal**: Verify AC switches to DRY mode when humidity is high and cooling is not needed

**Steps**:
1. Set thermostat to COOL mode
2. Set target temperature to match current room temperature (or slightly below)
3. Set humidity sensor to a value above threshold (e.g., 65% with 60% threshold)
4. Wait for the control cycle (typically 5 minutes)

**Expected Result**:
- HVAC mode switches to DRY
- Temperature reason shows "humidity_high"
- `humidity_manager.is_humidity_too_high` is `true`

**Verify**:
```yaml
# In Developer Tools → States, check:
climate.your_thermostat:
  hvac_mode: dry
  temperature_reason: humidity_high
  humidity_manager:
    is_humidity_too_high: true
    current_humidity: 65.0
    humidity_threshold: 60.0
```

##### Scenario 2: Cooling Override
**Goal**: Verify COOL mode takes priority when temperature rises

**Steps**:
1. Start with Scenario 1 (DRY mode active)
2. Increase room temperature above target (or lower target temperature)
3. Wait for the control cycle

**Expected Result**:
- HVAC mode switches back to COOL
- Temperature control takes priority over humidity

**Verify**:
```yaml
climate.your_thermostat:
  hvac_mode: cool
  # temperature_reason may change to something else
```

##### Scenario 3: Humidity Below Threshold
**Goal**: Verify DRY mode is not activated when humidity is normal

**Steps**:
1. Set thermostat to COOL mode
2. Set target temperature to match current room temperature
3. Set humidity sensor to a value below threshold (e.g., 55% with 60% threshold)

**Expected Result**:
- HVAC mode stays in COOL
- No DRY mode activation

##### Scenario 4: Non-COOL Mode
**Goal**: Verify humidity control doesn't activate in HEAT mode

**Steps**:
1. Set thermostat to HEAT mode
2. Set humidity sensor above threshold

**Expected Result**:
- HVAC mode stays in HEAT
- Humidity control doesn't interfere

##### Scenario 5: Sensor Unavailable
**Goal**: Verify graceful handling when sensor is unavailable

**Steps**:
1. Configure humidity feature with a sensor
2. Make the sensor unavailable (unavailable state)
3. Check thermostat behavior

**Expected Result**:
- Thermostat continues to work normally
- No errors in logs
- `current_humidity` shows `null` or `None`

### 3. Testing with Developer Tools

#### Check Humidity Manager State

In Developer Tools → States, find your thermostat and check:

```yaml
climate.your_thermostat:
  # ... other attributes ...
  is_humidity_configured: true
  humidity_manager:
    humidity_sensor_entity_id: sensor.your_humidity_sensor
    current_humidity: 65.0
    humidity_threshold: 60.0
    is_humidity_too_high: true
```

#### Simulate Humidity Changes

You can use `input_number` to simulate humidity changes:

1. Create an `input_number`:
```yaml
# In configuration.yaml
input_number:
  test_humidity:
    name: Test Humidity
    min: 0
    max: 100
    step: 1
    unit_of_measurement: "%"
```

2. Configure VTherm to use `input_number.test_humidity` as humidity sensor

3. Change the value in Developer Tools → Services:
```yaml
service: input_number.set_value
target:
  entity_id: input_number.test_humidity
data:
  value: 70  # High humidity
```

4. Watch the thermostat switch to DRY mode

### 4. Logging and Debugging

Enable debug logging to see humidity control in action:

```yaml
# In configuration.yaml
logger:
  default: info
  logs:
    custom_components.versatile_thermostat: debug
    custom_components.versatile_thermostat.feature_humidity_manager: debug
    custom_components.versatile_thermostat.state_manager: debug
```

Look for log messages like:
```
INFO - HumidityManager-YourThermostat - Humidity changed from 55.0% to 65.0%
INFO - YourThermostat - Humidity is high and cooling is not needed. Switching to DRY mode.
```

### 5. Integration Test Checklist

- [ ] Humidity feature can be enabled/disabled in config flow
- [ ] Humidity sensor can be selected from entity picker
- [ ] Humidity threshold can be configured (default: 60%)
- [ ] Central config option works (if applicable)
- [ ] DRY mode activates when:
  - [ ] AC mode is enabled
  - [ ] Requested mode is COOL
  - [ ] Humidity > threshold
  - [ ] Cooling not needed (on_percent <= 0.05)
  - [ ] DRY mode is available
- [ ] COOL mode overrides DRY when:
  - [ ] Temperature rises above target
  - [ ] Cooling is needed (on_percent > 0.05)
- [ ] Humidity control doesn't interfere with:
  - [ ] HEAT mode
  - [ ] Window detection
  - [ ] Safety mode
  - [ ] Auto start/stop
- [ ] Sensor unavailable state is handled gracefully
- [ ] Custom attributes are correctly exposed
- [ ] State manager correctly calculates HVAC mode with humidity

## Troubleshooting

### DRY Mode Not Activating

1. **Check AC Mode**: Ensure `ac_mode` is enabled
2. **Check DRY Support**: Verify underlying AC supports DRY mode
3. **Check Humidity**: Verify sensor reading is above threshold
4. **Check Cooling Need**: Ensure `on_percent <= 0.05` (temperature at target)
5. **Check Logs**: Look for humidity-related log messages

### COOL Mode Not Overriding DRY

1. **Check Temperature**: Ensure room temp is above target
2. **Check on_percent**: Should be > 0.05 when cooling needed
3. **Check Logs**: Verify state manager is calculating correctly

### Sensor Not Working

1. **Check Entity ID**: Verify sensor entity exists and is accessible
2. **Check State**: Sensor should provide numeric percentage value
3. **Check Availability**: Sensor should not be `unavailable` or `unknown`

## Performance Testing

- Test with rapid humidity changes (sensor updates every few seconds)
- Test with multiple thermostats using the same humidity sensor
- Test with central configuration for multiple thermostats
- Test during high system load

## Notes

- The humidity control feature only works with AC mode thermostats
- DRY mode must be supported by the underlying AC device
- Cooling always takes priority over dehumidification
- The default threshold is 60%, but can be adjusted per thermostat
- Humidity sensor should provide values as percentage (0-100%)
