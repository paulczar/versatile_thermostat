# Plan: Virtual Air Conditioner for Versatile Thermostat Testing

## Overview

Develop a fully-featured virtual air conditioner (AC) integration for Home Assistant that simulates a smart AC unit with multiple HVAC modes. This will serve as a safe, controllable backend for testing Versatile Thermostat functionality without real hardware constraints like cycle times, physical temperature changes, or safety concerns.

## Goals

1. **Instant Response**: No real cycle times - state changes happen immediately
2. **Full Feature Support**: Support all HVAC modes (heat, cool, dry, fan_only, auto, off)
3. **Realistic Simulation**: Simulate temperature changes, humidity changes, and AC behavior
4. **Configurable**: Adjustable parameters for different test scenarios
5. **Safe Testing**: No risk of damaging real equipment or wasting energy
6. **Integration Ready**: Works seamlessly as a backend for Versatile Thermostat

## Architecture

### Component Structure

```
virtual_ac/
├── __init__.py
├── manifest.json
├── config_flow.py
├── climate.py          # Main climate entity
├── sensor.py           # Temperature/humidity sensors (optional)
├── const.py            # Constants
└── strings.json        # Translations
```

### Core Components

1. **Virtual AC Climate Entity**
   - Implements Home Assistant ClimateEntity
   - Supports all standard HVAC modes
   - Configurable target temperature
   - Simulated current temperature
   - Simulated current humidity

2. **State Simulation Engine**
   - Simulates temperature changes based on HVAC mode
   - Simulates humidity changes (especially for DRY mode)
   - Configurable simulation speed (for testing different scenarios)
   - Optional realistic delays (can be disabled for fast testing)

3. **Configuration Options**
   - Initial temperature
   - Initial humidity
   - Room size (affects temperature change rate)
   - Insulation factor (affects heat loss/gain)
   - AC efficiency (affects cooling/heating rate)
   - Enable/disable realistic delays
   - Simulation speed multiplier

## Features

### Required Features

1. **HVAC Modes**
   - `off`: No operation, temperature drifts toward ambient
   - `cool`: Cools room, decreases temperature
   - `heat`: Heats room, increases temperature
   - `dry`: Dehumidifies, decreases humidity, slight cooling
   - `fan_only`: Air circulation only, no temperature change
   - `auto`: Automatically switches between heat/cool based on target

2. **Temperature Control**
   - Target temperature setting
   - Current temperature (simulated)
   - Temperature precision (0.1°C or 1°F)
   - Min/max temperature limits
   - Temperature unit (Celsius/Fahrenheit)

3. **Humidity Support**
   - Current humidity (simulated)
   - Humidity changes based on mode:
     - DRY mode: Decreases humidity
     - COOL mode: Slight humidity decrease
     - HEAT mode: Slight humidity decrease
     - FAN_ONLY: No humidity change

4. **Preset Modes** (Optional)
   - `eco`: Energy-saving mode
   - `comfort`: Standard comfort mode
   - `sleep`: Quiet, energy-efficient mode
   - `away`: Minimal operation mode

5. **Fan Speed Control** (Optional)
   - `auto`, `low`, `medium`, `high`
   - Affects temperature change rate

6. **Swing Mode** (Optional)
   - `on`, `off`
   - Visual indicator only (no functional impact)

### Simulation Behavior

1. **Temperature Simulation**
   ```
   When COOL mode active:
     - Temperature decreases toward target
     - Rate: configurable (e.g., 0.5°C per minute)
     - Stops at target or slightly below

   When HEAT mode active:
     - Temperature increases toward target
     - Rate: configurable (e.g., 0.5°C per minute)
     - Stops at target or slightly above

   When DRY mode active:
     - Temperature decreases slightly (less than COOL)
     - Humidity decreases significantly
     - Rate: configurable

   When OFF mode:
     - Temperature drifts toward ambient (configurable)
     - Rate: slower than active modes
   ```

2. **Humidity Simulation**
   ```
   When DRY mode active:
     - Humidity decreases toward lower threshold
     - Rate: configurable (e.g., 2% per minute)

   When COOL mode active:
     - Humidity decreases slightly (condensation)
     - Rate: slower than DRY mode

   When other modes:
     - Humidity remains stable or drifts slowly
   ```

3. **Instant vs Realistic Mode**
   - **Instant Mode** (default for testing):
     - State changes happen immediately
     - Temperature/humidity jump to target instantly
     - No simulation delays

   - **Realistic Mode** (optional):
     - Simulates gradual temperature/humidity changes
     - Configurable update interval (e.g., every 10 seconds)
     - More realistic but slower for testing

## Implementation Plan

### Phase 1: Basic Climate Entity (Week 1)

1. **Setup Integration Structure**
   - Create integration directory structure
   - Set up manifest.json with required metadata
   - Create config_flow.py for UI configuration
   - Basic strings.json for translations

2. **Core Climate Entity**
   - Implement basic ClimateEntity class
   - Support OFF, COOL, HEAT modes initially
   - Basic temperature get/set
   - No simulation yet - just state management

3. **Configuration Flow**
   - UI for creating virtual AC instances
   - Basic configuration options:
     - Name
     - Initial temperature
     - Initial humidity
     - Temperature unit

**Deliverable**: Working virtual AC that can be added via UI, supports basic modes, can be controlled by Versatile Thermostat

### Phase 2: Full HVAC Mode Support (Week 1-2)

1. **Add Remaining Modes**
   - Implement DRY mode
   - Implement FAN_ONLY mode
   - Implement AUTO mode logic

2. **Humidity Support**
   - Add current_humidity property
   - Implement humidity simulation for DRY mode
   - Add humidity to state attributes

3. **State Management**
   - Proper state updates when mode changes
   - State persistence across restarts
   - State attributes for debugging

**Deliverable**: Full HVAC mode support with humidity simulation

### Phase 3: Temperature Simulation (Week 2)

1. **Simulation Engine**
   - Create background task for temperature updates
   - Implement temperature change logic per mode
   - Configurable change rates

2. **Realistic Behavior**
   - Temperature approaches target but may overshoot slightly
   - Different rates for different modes
   - Ambient temperature drift when OFF

3. **Configuration Options**
   - Add simulation speed multiplier
   - Add room size/insulation factors
   - Enable/disable realistic mode

**Deliverable**: Realistic temperature simulation with configurable parameters

### Phase 4: Advanced Features (Week 2-3)

1. **Preset Modes**
   - Implement ECO, COMFORT, SLEEP, AWAY presets
   - Each preset affects target temperature and behavior

2. **Fan Speed Control**
   - Add fan speed attribute
   - Fan speed affects temperature change rate
   - Visual feedback in UI

3. **Swing Mode**
   - Add swing mode attribute
   - Visual indicator only

4. **State Attributes**
   - Add detailed state attributes for debugging:
     - Simulation mode (instant/realistic)
     - Current change rate
     - Time since last mode change
     - Target vs current temperature difference

**Deliverable**: Full-featured virtual AC with all standard climate features

### Phase 5: Testing & Documentation (Week 3)

1. **Unit Tests**
   - Test mode switching
   - Test temperature simulation
   - Test humidity simulation
   - Test configuration options

2. **Integration Tests**
   - Test with Versatile Thermostat
   - Test all HVAC modes
   - Test DRY mode humidity control
   - Test temperature threshold scenarios

3. **Documentation**
   - README with setup instructions
   - Configuration guide
   - Testing scenarios guide
   - Troubleshooting guide

**Deliverable**: Fully tested and documented virtual AC integration

## Configuration Schema

### Config Flow Options

```python
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Optional("initial_temp", default=22.0): vol.Coerce(float),
    vol.Optional("initial_humidity", default=50.0): vol.Coerce(float),
    vol.Optional("temp_unit", default="celsius"): vol.In(["celsius", "fahrenheit"]),
    vol.Optional("min_temp", default=16.0): vol.Coerce(float),
    vol.Optional("max_temp", default=30.0): vol.Coerce(float),
    vol.Optional("precision", default=0.1): vol.Coerce(float),
})

STEP_ADVANCED_DATA_SCHEMA = vol.Schema({
    vol.Optional("simulation_mode", default="instant"): vol.In(["instant", "realistic"]),
    vol.Optional("cooling_rate", default=0.5): vol.Coerce(float),  # °C per minute
    vol.Optional("heating_rate", default=0.5): vol.Coerce(float),  # °C per minute
    vol.Optional("dry_humidity_rate", default=2.0): vol.Coerce(float),  # % per minute
    vol.Optional("ambient_temp", default=20.0): vol.Coerce(float),
    vol.Optional("ambient_drift_rate", default=0.1): vol.Coerce(float),  # °C per minute when OFF
    vol.Optional("update_interval", default=10): vol.Coerce(int),  # seconds
})
```

## Technical Implementation Details

### Climate Entity Class Structure

```python
class VirtualACClimate(ClimateEntity):
    """Virtual Air Conditioner Climate Entity."""

    # Required properties
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT,
                        HVACMode.DRY, HVACMode.FAN_ONLY, HVACMode.AUTO]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE |
        ClimateEntityFeature.FAN_MODE |
        ClimateEntityFeature.PRESET_MODE |
        ClimateEntityFeature.SWING_MODE
    )

    # State properties
    _attr_current_temperature: float
    _attr_current_humidity: float
    _attr_target_temperature: float
    _attr_hvac_mode: HVACMode
    _attr_fan_mode: str
    _attr_preset_mode: str
    _attr_swing_mode: str

    # Simulation
    _simulation_task: asyncio.Task | None = None
    _simulation_mode: str = "instant"
    _last_update: datetime

    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        """Set HVAC mode."""
        # Instant mode: update immediately
        # Realistic mode: start simulation task

    async def async_set_temperature(self, **kwargs):
        """Set target temperature."""

    async def _simulation_loop(self):
        """Background task for realistic simulation."""
        # Update temperature/humidity based on current mode
        # Respect update_interval
        # Apply change rates
```

### State Updates

- Use `self.async_write_ha_state()` to update state
- Update every `update_interval` seconds in realistic mode
- Update immediately on mode/temperature changes in instant mode
- Store state in `self.hass.data[DOMAIN][entry.entry_id]` for persistence

### Integration with Versatile Thermostat

1. **Entity Selection**: Virtual AC appears in Versatile Thermostat config flow as a climate entity
2. **Mode Support**: All modes supported, especially DRY mode for humidity testing
3. **State Reading**: Versatile Thermostat reads current_temperature, current_humidity, hvac_mode
4. **Control**: Versatile Thermostat sets hvac_mode and target_temperature

## Testing Scenarios

### Scenario 1: Basic Mode Switching
- Switch between COOL, HEAT, DRY, OFF
- Verify state updates immediately
- Verify temperature/humidity changes appropriately

### Scenario 2: Temperature Control
- Set target temperature
- Verify current temperature approaches target
- Test overshoot behavior

### Scenario 3: DRY Mode Humidity Control
- Set to DRY mode with high humidity
- Verify humidity decreases
- Verify temperature decreases slightly
- Test with Versatile Thermostat humidity control

### Scenario 4: Versatile Thermostat Integration
- Configure Versatile Thermostat to use Virtual AC
- Test all Versatile Thermostat features:
  - DRY mode activation on high humidity
  - COOL mode priority over DRY
  - Temperature threshold behavior
  - Mode switching

### Scenario 5: Realistic vs Instant Mode
- Test in instant mode (fast testing)
- Test in realistic mode (more realistic behavior)
- Verify both work correctly

## Benefits

1. **Safe Testing**: No risk to real equipment
2. **Fast Testing**: Instant mode allows rapid test cycles
3. **Controlled Environment**: Predictable, repeatable behavior
4. **Full Feature Support**: Test all HVAC modes and features
5. **No Cycle Time Constraints**: Test immediately without waiting
6. **Cost Effective**: No energy costs for testing
7. **Reproducible**: Same conditions every time

## Future Enhancements

1. **Multiple Virtual ACs**: Support multiple instances for multi-zone testing
2. **Weather Integration**: Simulate ambient temperature based on weather
3. **Energy Tracking**: Simulate energy consumption for testing energy features
4. **Historical Data**: Store temperature/humidity history for analysis
5. **Webhook Support**: Allow external control via webhooks
6. **REST API**: Expose control via REST API for automated testing

## Dependencies

- Home Assistant Core (climate platform)
- Python asyncio for simulation tasks
- Standard Home Assistant integration requirements

## Timeline

- **Week 1**: Basic climate entity + core modes
- **Week 2**: Simulation engine + full mode support
- **Week 3**: Advanced features + testing + documentation

**Total Estimated Time**: 3 weeks for full implementation

## Success Criteria

1. ✅ Virtual AC can be added via UI
2. ✅ All HVAC modes work correctly
3. ✅ Temperature and humidity simulation works
4. ✅ Versatile Thermostat can control Virtual AC
5. ✅ DRY mode humidity control works with Versatile Thermostat
6. ✅ Instant mode allows fast testing
7. ✅ Realistic mode provides realistic behavior
8. ✅ Well documented and tested



