# Real-World Testing Guide: Humidity Control Feature

This document provides step-by-step instructions for testing the humidity control feature in a real Home Assistant environment. These tests verify that the thermostat correctly switches between COOL and DRY modes based on humidity levels and temperature conditions.

## Automated Testing

For automated testing, see the scripts in `scripts/` directory:

- **Python Script** (`scripts/test_humidity_control.py`): Comprehensive automated test suite with detailed logging
- **YAML Script** (`scripts/humidity_test_automation.yaml`): Simple Home Assistant script for basic testing
- **Documentation** (`scripts/README_HUMIDITY_TESTING.md`): Complete guide for automated testing

The automated scripts run all test scenarios and log results to a file. For manual testing and detailed understanding, continue reading this document.

## Prerequisites

Before starting, ensure you have:

1. **Home Assistant** running with Versatile Thermostat integration installed
2. **AC Mode Thermostat** (`over_climate` type) configured and working
3. **Underlying AC Device** that supports DRY mode
4. **Humidity Sensor** configured and providing readings (or use `input_number` for testing)
5. **Temperature Sensor** providing accurate room temperature readings
6. **Access to Developer Tools** in Home Assistant UI

## Understanding the Feature

The humidity control feature automatically switches your AC to DRY mode when:
- ✅ AC is in **COOL mode**
- ✅ **Humidity exceeds threshold** (default: 60%)
- ✅ **Temperature is at or near target** (within 0.1°C) - cooling is not actively needed
- ✅ **DRY mode is available** in your AC device

**Important**: Temperature control always takes priority. If cooling is needed (temperature > target + 0.1°C), the AC stays in COOL mode even if humidity is high.

## Test Setup

### Step 1: Configure Humidity Sensor

If you don't have a real humidity sensor, create a test sensor using `input_number`:

1. Go to **Settings → Add-ons → File editor** (or edit `configuration.yaml` directly)
2. Add the following:

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

3. **Restart Home Assistant** to load the new configuration
4. Verify the sensor appears in **Developer Tools → States** as `input_number.test_humidity`

### Step 2: Configure Thermostat with Humidity Feature

1. Go to **Settings → Devices & Services → Versatile Thermostat**
2. **Create a new thermostat** or **Edit existing** (must be `over_climate` type)
3. During configuration:
   - Select **"Climate"** as thermostat type
   - Enable **AC mode**
   - In **Features** step, enable **"Use humidity management"**
   - In **Humidity management** step:
     - Select your humidity sensor (`input_number.test_humidity` or your real sensor)
     - Set **Humidity threshold** (default: 60%)
4. **Complete the configuration** and verify the thermostat appears in your entities

### Step 3: Verify Initial Configuration

1. Go to **Developer Tools → States**
2. Find your thermostat entity (e.g., `climate.living_room_ac`)
3. Check the following attributes:

```yaml
climate.living_room_ac:
  hvac_modes: [heat, cool, dry, off]  # Must include 'dry'
  ac_mode: true
  is_humidity_configured: true
  humidity_manager:
    humidity_sensor_entity_id: input_number.test_humidity
    current_humidity: 55.0
    humidity_threshold: 60.0
    is_humidity_too_high: false
  specific_states:
    current_humidity: 55.0  # Should match humidity_manager.current_humidity
```

**✅ If all attributes are present and correct, proceed to testing**

## Test Scenarios

### Test Scenario 1: DRY Mode Activation (Humidity High, Temperature at Target)

**Objective**: Verify AC switches to DRY mode when humidity is high and cooling is not needed.

#### Initial Conditions
- **Thermostat Mode**: COOL
- **Target Temperature**: 22°C (or match your current room temperature)
- **Current Room Temperature**: 22.0°C (or within 0.1°C of target)
- **Humidity**: 55% (below threshold)

#### Test Steps

1. **Set thermostat to COOL mode**:
   - Go to **Developer Tools → Services**
   - Service: `climate.set_hvac_mode`
   - Entity: `climate.your_thermostat`
   - Service Data: `{"hvac_mode": "cool"}`
   - Click **CALL SERVICE**

2. **Verify initial state**:
   - Check **Developer Tools → States** → `climate.your_thermostat`
   - Expected: `hvac_mode: cool`
   - Expected: `hvac_reason: null` or not present

3. **Set target temperature to match current room temperature**:
   - Service: `climate.set_temperature`
   - Entity: `climate.your_thermostat`
   - Service Data: `{"temperature": 22.0}` (adjust to your room temp)
   - Click **CALL SERVICE**

4. **Wait for temperature to stabilize** (if needed):
   - Monitor `specific_states.ema_temp` in States
   - Ensure it's within 0.1°C of target temperature

5. **Increase humidity above threshold**:
   - Service: `input_number.set_value`
   - Entity: `input_number.test_humidity`
   - Service Data: `{"value": 65.0}` (above 60% threshold)
   - Click **CALL SERVICE**

6. **Wait for control cycle** (typically 5 minutes, or force refresh):
   - Service: `climate.set_temperature` (any small change to trigger update)
   - Or wait for the next automatic cycle

7. **Verify DRY mode activation**:
   - Check **Developer Tools → States** → `climate.your_thermostat`
   - Expected: `hvac_mode: dry`
   - Expected: `hvac_reason: "DRY mode: Humidity too high"` (in `specific_states.messages`)
   - Expected: `humidity_manager.is_humidity_too_high: true`
   - Expected: `humidity_manager.current_humidity: 65.0`
   - Expected: `specific_states.current_humidity: 65.0`

#### Expected Log Messages

Check **Settings → System → Logs** for:
```
INFO - HumidityManager-YourThermostat - Humidity changed from 55.0% to 65.0%
INFO - HumidityManager-YourThermostat - Humidity too high (65.0% > 60.0%), temperature at target (22.0°C), switching to DRY mode
```

#### ✅ Success Criteria
- [ ] HVAC mode changed from `cool` to `dry`
- [ ] `hvac_reason` shows humidity-related message
- [ ] `humidity_manager.is_humidity_too_high` is `true`
- [ ] `current_humidity` attribute shows correct value (65.0%)
- [ ] Log messages confirm the switch

---

### Test Scenario 2: COOL Mode Priority (Humidity High, But Cooling Needed)

**Objective**: Verify COOL mode takes priority when temperature rises, even if humidity is high.

#### Initial Conditions
- **Thermostat Mode**: DRY (from Scenario 1)
- **Target Temperature**: 22°C
- **Current Room Temperature**: 22.0°C
- **Humidity**: 65% (above threshold)

#### Test Steps

1. **Verify DRY mode is active** (from Scenario 1):
   - Check States → `hvac_mode: dry`

2. **Lower target temperature** (or simulate temperature rise):
   - Service: `climate.set_temperature`
   - Entity: `climate.your_thermostat`
   - Service Data: `{"temperature": 20.0}` (2°C below current)
   - Click **CALL SERVICE**

   **OR** if you can simulate temperature rise:
   - Increase room temperature sensor reading to 22.5°C or higher

3. **Wait for control cycle** (5 minutes or force refresh)

4. **Verify COOL mode activation**:
   - Check **Developer Tools → States** → `climate.your_thermostat`
   - Expected: `hvac_mode: cool`
   - Expected: `hvac_reason: null` (cleared when using requested mode)
   - Expected: `humidity_manager.is_humidity_too_high: true` (still true, but ignored)
   - Expected: `humidity_manager.current_humidity: 65.0` (still high)

#### Expected Log Messages

Check logs for:
```
INFO - HumidityManager-YourThermostat - Humidity too high (65.0% > 60.0%), but cooling is still needed (temp 22.5°C > target 20.0°C), keeping COOL mode
```

#### ✅ Success Criteria
- [ ] HVAC mode changed from `dry` to `cool`
- [ ] `hvac_reason` is cleared/null
- [ ] Temperature control takes priority over humidity
- [ ] Log confirms cooling is needed

---

### Test Scenario 3: DRY Mode Deactivation (Humidity Drops Below Threshold)

**Objective**: Verify AC switches back to COOL mode when humidity drops below threshold.

#### Initial Conditions
- **Thermostat Mode**: DRY (from Scenario 1)
- **Target Temperature**: 22°C
- **Current Room Temperature**: 22.0°C (at target)
- **Humidity**: 65% (above threshold)

#### Test Steps

1. **Verify DRY mode is active**:
   - Check States → `hvac_mode: dry`
   - Check `humidity_manager.is_humidity_too_high: true`

2. **Decrease humidity below threshold**:
   - Service: `input_number.set_value`
   - Entity: `input_number.test_humidity`
   - Service Data: `{"value": 55.0}` (below 60% threshold)
   - Click **CALL SERVICE**

3. **Wait for control cycle** (5 minutes or force refresh)

4. **Verify COOL mode activation**:
   - Check **Developer Tools → States** → `climate.your_thermostat`
   - Expected: `hvac_mode: cool`
   - Expected: `hvac_reason: null`
   - Expected: `humidity_manager.is_humidity_too_high: false`
   - Expected: `humidity_manager.current_humidity: 55.0`

#### Expected Log Messages

Check logs for:
```
INFO - HumidityManager-YourThermostat - Humidity changed from 65.0% to 55.0%
```

#### ✅ Success Criteria
- [ ] HVAC mode changed from `dry` to `cool`
- [ ] `humidity_manager.is_humidity_too_high` is `false`
- [ ] `hvac_reason` is cleared
- [ ] Log confirms humidity change

---

### Test Scenario 4: Temperature Threshold Boundary Test

**Objective**: Verify the 0.1°C temperature threshold works correctly.

#### Test Steps

**Part A: Temperature at Target (0.0°C difference) - Should Use DRY**

1. Set conditions:
   - Target: 22.0°C
   - Current: 22.0°C
   - Humidity: 65% (above threshold)
   - Mode: COOL

2. Wait for control cycle

3. **Expected**: `hvac_mode: dry` ✅

**Part B: Temperature Just Below Threshold (0.05°C difference) - Should Use DRY**

1. Set conditions:
   - Target: 22.0°C
   - Current: 22.05°C (within 0.1°C threshold)
   - Humidity: 65% (above threshold)
   - Mode: COOL

2. Wait for control cycle

3. **Expected**: `hvac_mode: dry` ✅

**Part C: Temperature Above Threshold (0.2°C difference) - Should Use COOL**

1. Set conditions:
   - Target: 22.0°C
   - Current: 22.2°C (above 0.1°C threshold)
   - Humidity: 65% (above threshold)
   - Mode: COOL

2. Wait for control cycle

3. **Expected**: `hvac_mode: cool` ✅ (cooling needed)

#### ✅ Success Criteria
- [ ] DRY mode activates when temp ≤ target + 0.1°C
- [ ] COOL mode stays active when temp > target + 0.1°C

---

### Test Scenario 5: Non-COOL Mode Ignored

**Objective**: Verify humidity control doesn't interfere with HEAT mode.

#### Test Steps

1. **Set thermostat to HEAT mode**:
   - Service: `climate.set_hvac_mode`
   - Service Data: `{"hvac_mode": "heat"}`

2. **Set high humidity**:
   - Service: `input_number.set_value`
   - Service Data: `{"value": 70.0}`

3. **Wait for control cycle**

4. **Verify HEAT mode remains**:
   - Check States → `hvac_mode: heat`
   - Expected: No DRY mode activation
   - Expected: `humidity_manager.is_humidity_too_high: true` (but ignored)

#### ✅ Success Criteria
- [ ] HVAC mode stays `heat`
- [ ] No DRY mode activation
- [ ] Humidity control doesn't interfere

---

### Test Scenario 6: DRY Mode Not Available

**Objective**: Verify graceful fallback when DRY mode is not supported.

#### Test Steps

1. **If your AC supports DRY mode**, temporarily disable it in the underlying AC device configuration

2. **Set conditions for DRY activation**:
   - Mode: COOL
   - Temperature: At target
   - Humidity: 65% (above threshold)

3. **Wait for control cycle**

4. **Verify COOL mode remains**:
   - Check States → `hvac_mode: cool`
   - Expected: No error, graceful fallback

#### ✅ Success Criteria
- [ ] No errors in logs
- [ ] COOL mode remains active
- [ ] System handles missing DRY mode gracefully

---

### Test Scenario 7: Sensor Unavailable Handling

**Objective**: Verify graceful handling when humidity sensor becomes unavailable.

#### Test Steps

1. **Set sensor to unavailable**:
   - Service: `input_number.set_value`
   - Entity: `input_number.test_humidity`
   - Service Data: `{"value": "unavailable"}` (or disable the sensor)

   **OR** use Developer Tools → States → set state to `unavailable`

2. **Wait for control cycle**

3. **Verify thermostat continues working**:
   - Check States → `humidity_manager.current_humidity: null` or `None`
   - Expected: No errors in logs
   - Expected: Thermostat continues normal operation

#### ✅ Success Criteria
- [ ] No errors in logs
- [ ] `current_humidity` shows `null`
- [ ] Thermostat continues normal operation
- [ ] No DRY mode activation (humidity unknown)

---

## Monitoring During Tests

### Key Attributes to Monitor

In **Developer Tools → States**, monitor these attributes:

```yaml
climate.your_thermostat:
  # Main state
  hvac_mode: cool | dry | heat | off

  # Humidity control
  humidity_manager:
    current_humidity: 55.0
    humidity_threshold: 60.0
    is_humidity_too_high: false

  # Standard climate attribute
  current_humidity: 55.0  # Exposed as standard attribute

  # State details
  specific_states:
    current_humidity: 55.0
    hvac_reason: "DRY mode: Humidity too high"  # When DRY is active
    messages: ["DRY mode: Humidity too high"]  # User-facing message
```

### Log Monitoring

Enable debug logging for detailed information:

```yaml
# In configuration.yaml
logger:
  default: info
  logs:
    custom_components.versatile_thermostat: debug
    custom_components.versatile_thermostat.feature_humidity_manager: debug
    custom_components.versatile_thermostat.state_manager: debug
```

Key log messages to watch for:

- `Humidity changed from X% to Y%` - Sensor updates
- `Humidity too high (X% > Y%), temperature at target (Z°C), switching to DRY mode` - DRY activation
- `Humidity too high (X% > Y%), but cooling is still needed (temp A°C > target B°C), keeping COOL mode` - COOL priority

## Troubleshooting

### DRY Mode Not Activating

**Checklist**:
1. ✅ AC mode is enabled (`ac_mode: true`)
2. ✅ Humidity feature is configured (`is_humidity_configured: true`)
3. ✅ Humidity sensor reading > threshold
4. ✅ Current temperature ≤ target + 0.1°C
5. ✅ Requested mode is COOL
6. ✅ DRY mode is available in `hvac_modes`
7. ✅ Check logs for error messages

### COOL Mode Not Overriding DRY

**Checklist**:
1. ✅ Current temperature > target + 0.1°C
2. ✅ Check `specific_states.ema_temp` vs `target_temperature`
3. ✅ Verify temperature sensor is updating correctly
4. ✅ Check logs for state manager calculations

### Sensor Not Working

**Checklist**:
1. ✅ Sensor entity exists and is accessible
2. ✅ Sensor provides numeric percentage (0-100)
3. ✅ Sensor state is not `unavailable` or `unknown`
4. ✅ Check `humidity_manager.humidity_sensor_entity_id` matches your sensor

## Test Checklist Summary

Use this checklist to verify all scenarios:

- [ ] **Scenario 1**: DRY mode activates when humidity high + temp at target
- [ ] **Scenario 2**: COOL mode takes priority when cooling needed
- [ ] **Scenario 3**: DRY mode deactivates when humidity drops
- [ ] **Scenario 4**: Temperature threshold (0.1°C) works correctly
- [ ] **Scenario 5**: Humidity control doesn't interfere with HEAT mode
- [ ] **Scenario 6**: Graceful handling when DRY mode unavailable
- [ ] **Scenario 7**: Graceful handling when sensor unavailable
- [ ] **Attributes**: `current_humidity` exposed correctly
- [ ] **Attributes**: `hvac_reason` shows correct message
- [ ] **Logs**: Appropriate log messages appear
- [ ] **Performance**: No errors or warnings in logs

## Notes

- **Control Cycle**: The thermostat typically updates every 5 minutes. You can force an update by making any small change to the thermostat settings.
- **Temperature Comparison**: Uses EMA (Exponential Moving Average) temperature, not instantaneous reading, for stability.
- **Threshold**: Default is 60%, but can be adjusted per thermostat in configuration.
- **Priority**: Temperature control **always** takes priority over humidity control.
- **Mode Availability**: DRY mode must be supported by your underlying AC device.

## Real-World Usage Tips

1. **Adjust Threshold**: 60% is a good default, but adjust based on:
   - Your comfort preferences
   - Local climate conditions
   - Seasonal variations

2. **Monitor Performance**: Watch your energy usage - DRY mode is typically more energy-efficient than COOL mode for dehumidification.

3. **Temperature Settings**: Keep target temperature reasonable - the feature works best when you're not constantly changing the target.

4. **Sensor Placement**: Ensure your humidity sensor is placed away from:
   - Direct airflow from AC vents
   - Windows and doors
   - Heat sources

5. **Multiple Zones**: If you have multiple thermostats, each can have its own humidity sensor and threshold.
