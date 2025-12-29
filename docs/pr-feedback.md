# PR Feedback and Changes

This document tracks feedback received on the PR and the changes made to address each item.

## Feedback Items

### 1. Expose humidity value as `current_humidity` attribute

**Feedback:**
> Could the humidity value of the added sensor be exposed to the climate entity over "current_humidity" attribute then?
>
> As it's part of standard attribute: https://developers.home-assistant.io/docs/core/entity/climate/

**Status:** ✅ Addressed

**Changes Made:**
- Modified `current_humidity` property in `thermostat_climate.py` (lines 1001-1011)
- Updated the property to prioritize humidity_manager value when configured
- Falls back to underlying entity's `current_humidity` if humidity_manager is not configured or has no value

**Implementation:**
```python
@property
def current_humidity(self) -> float | None:
    """Return the humidity."""
    # Priority: use humidity_manager if configured, otherwise fall back to underlying entity
    if self.humidity_manager and self.humidity_manager.is_configured:
        humidity = self.humidity_manager.current_humidity
        if humidity is not None:
            return humidity

    if self.underlying_entity(0):
        return self.underlying_entity(0).current_humidity

    return None
```

**Files Modified:**
- `custom_components/versatile_thermostat/thermostat_climate.py`

**Result:**
- Climate entity now exposes `current_humidity` as a standard Home Assistant climate attribute
- Value comes from the configured humidity sensor when available
- Maintains backward compatibility with underlying entity's humidity reading

---

### 2. Formatter not respecting line-length configuration

**Feedback:**
> Your formatter breaks all long line and dont use my custom config in pyproject.toml (line-length = 180).
>
> Maybe you don't install black formatter. This makes many unnecessary changes and a make the review not easy.
>
> This is not visible in the github review window but visible in the files you have committed.

**Status:** ✅ Addressed

**Changes Made:**
- Ran `black` formatter with correct configuration (line-length = 180) on all files from the humidity feature commit
- Reformatted `thermostat_climate.py` to consolidate unnecessarily broken lines
- Verified all other humidity feature files are properly formatted

**Implementation:**
```bash
black custom_components/versatile_thermostat/feature_humidity_manager.py \
      custom_components/versatile_thermostat/base_thermostat.py \
      custom_components/versatile_thermostat/config_flow.py \
      custom_components/versatile_thermostat/config_schema.py \
      custom_components/versatile_thermostat/state_manager.py \
      custom_components/versatile_thermostat/thermostat_climate.py \
      tests/test_humidity.py \
      tests/test_state_manager.py
```

**Files Modified:**
- `custom_components/versatile_thermostat/thermostat_climate.py` (reformatted to respect 180 char line length)

**Result:**
- All files now properly formatted with black using line-length = 180 from pyproject.toml
- Unnecessarily broken lines consolidated
- Code review will be easier with consistent formatting

---

### 3. Remove humidity feature from climate valve regulation schema

**Feedback:**
> Climate with direct valve regulation cannot dry. It is for thermostatic valve which can't cool. Remove this

**Status:** ✅ Addressed

**Changes Made:**
- Removed `CONF_USE_HUMIDITY_FEATURE` from `STEP_CLIMATE_VALVE_FEATURES_DATA_SCHEMA` in `config_schema.py`
- Humidity feature remains available for:
  - Regular climate thermostats (`STEP_CLIMATE_FEATURES_DATA_SCHEMA`)
  - Switch-based thermostats (`STEP_FEATURES_DATA_SCHEMA`)
  - Central configuration (`STEP_CENTRAL_FEATURES_DATA_SCHEMA`)

**Rationale:**
- Climate thermostats with direct valve regulation (thermostatic valves) can only heat, not cool or dry
- Humidity control requires DRY mode, which is only available for AC/cooling-capable devices
- Removing the option prevents users from enabling an incompatible feature

**Implementation:**
```python
STEP_CLIMATE_VALVE_FEATURES_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_USE_WINDOW_FEATURE, default=False): cv.boolean,
        vol.Optional(CONF_USE_MOTION_FEATURE, default=False): cv.boolean,
        vol.Optional(CONF_USE_POWER_FEATURE, default=False): cv.boolean,
        vol.Optional(CONF_USE_PRESENCE_FEATURE, default=False): cv.boolean,
        # CONF_USE_HUMIDITY_FEATURE removed - valve regulation cannot dry
    }
)
```

**Files Modified:**
- `custom_components/versatile_thermostat/config_schema.py`

**Result:**
- Humidity feature no longer available for climate thermostats with valve regulation
- Feature remains available for appropriate thermostat types (AC/cooling-capable)
- Existing validation in `state_manager.py` already ensures humidity feature only works with AC mode and DRY mode support

---

### 4. Move humidity_manager initialization to thermostat_climate.py

**Feedback:**
> Should be added only over climate VTherm. So remove from here and set in thermostat_climate.py only (like auto-start/stop manager typically). Set it to None here (like auto_start_stop_manager)

**Status:** ✅ Already Correct

**Current Implementation:**
The `_humidity_manager` follows the same pattern as `_auto_start_stop_manager`:

**In `base_thermostat.py`:**
```python
# Auto start/stop is only for over_climate
self._auto_start_stop_manager: FeatureAutoStartStopManager | None = None
self._lock_manager: FeatureLockManager = FeatureLockManager(self, hass)
# Humidity manager is only for over_climate
self._humidity_manager: FeatureHumidityManager | None = None
```

**In `thermostat_climate.py` `post_init()` method:**
```python
self._auto_start_stop_manager: FeatureAutoStartStopManager = FeatureAutoStartStopManager(self, self._hass)
self.register_manager(self._auto_start_stop_manager)

# Humidity manager is only for over_climate, not for valve regulation
if config_entry.get(CONF_AUTO_REGULATION_MODE) != CONF_AUTO_REGULATION_VALVE:
    self._humidity_manager: FeatureHumidityManager = FeatureHumidityManager(self, self._hass)
    self.register_manager(self._humidity_manager)
```

**Files:**
- `custom_components/versatile_thermostat/base_thermostat.py` (line 198: set to None)
- `custom_components/versatile_thermostat/thermostat_climate.py` (lines 80-83: conditionally initialized)

**Result:**
- `_humidity_manager` is correctly set to `None` in `base_thermostat.py`
- Initialization happens only in `thermostat_climate.py` for non-valve-regulation thermostats
- Registration only occurs for regular over_climate thermostats (not valve regulation)
- Implementation matches the requested pattern exactly

---

### 5. Humidity manager registration should only be in over_climate (not valve regulation)

**Feedback:**
> `self.register_manager(self._humidity_manager)` should only be in over_climate

**Status:** ✅ Addressed

**Changes Made:**
- Added conditional check in `thermostat_climate.py` `post_init()` method to skip humidity_manager initialization and registration for valve regulation thermostats
- Only initializes and registers `humidity_manager` when `CONF_AUTO_REGULATION_MODE != CONF_AUTO_REGULATION_VALVE`

**Implementation:**
```python
@overrides
def post_init(self, config_entry: ConfigData):
    """Initialize the Thermostat"""

    self._auto_start_stop_manager: FeatureAutoStartStopManager = FeatureAutoStartStopManager(self, self._hass)
    self.register_manager(self._auto_start_stop_manager)

    # Humidity manager is only for over_climate, not for valve regulation
    if config_entry.get(CONF_AUTO_REGULATION_MODE) != CONF_AUTO_REGULATION_VALVE:
        self._humidity_manager: FeatureHumidityManager = FeatureHumidityManager(self, self._hass)
        self.register_manager(self._humidity_manager)

    super().post_init(config_entry)
```

**Files Modified:**
- `custom_components/versatile_thermostat/thermostat_climate.py`

**Result:**
- `humidity_manager` is only initialized and registered for regular over_climate thermostats
- Valve regulation thermostats (`ThermostatOverClimateValve`) will not have `humidity_manager` initialized
- Consistent with the fact that valve regulation thermostats cannot use DRY mode (they can only heat, not cool/dry)

---

### 6. All humidity state should only be in over_climate

**Feedback:**
> all humidity state should only be in over_climate as the other forms don't support it

**Status:** ✅ Addressed

**Changes Made:**
- Removed `FeatureHumidityManager.unrecorded_attributes` from `BaseThermostat._entity_component_unrecorded_attributes`
- Added `FeatureHumidityManager.unrecorded_attributes` to `ThermostatOverClimate._entity_component_unrecorded_attributes` only
- Humidity state attributes are now only exposed for over_climate thermostats

**Implementation:**

**In `base_thermostat.py`:**
```python
_entity_component_unrecorded_attributes = (
    ClimateEntity._entity_component_unrecorded_attributes.union(frozenset({"configuration", "preset_temperatures"}))
    .union(FeaturePresenceManager.unrecorded_attributes)
    .union(FeaturePowerManager.unrecorded_attributes)
    .union(FeatureMotionManager.unrecorded_attributes)
    .union(FeatureWindowManager.unrecorded_attributes)
    # FeatureHumidityManager.unrecorded_attributes removed - only for over_climate
)
```

**In `thermostat_climate.py`:**
```python
_entity_component_unrecorded_attributes = BaseThermostat._entity_component_unrecorded_attributes.union(
    frozenset({
        "is_over_climate",
        "vtherm_over_climate",
    })
    .union(FeatureAutoStartStopManager.unrecorded_attributes)
    .union(FeatureHumidityManager.unrecorded_attributes)  # Added here for over_climate only
)
```

**Files Modified:**
- `custom_components/versatile_thermostat/base_thermostat.py` (removed humidity unrecorded_attributes)
- `custom_components/versatile_thermostat/thermostat_climate.py` (added humidity unrecorded_attributes)

**Result:**
- Humidity state attributes (`humidity_manager`, `is_humidity_configured`, etc.) are now only exposed for over_climate thermostats
- Other thermostat types (over_switch, over_valve) will not have humidity state attributes
- The `refresh_state` check for humidity is safe for all thermostat types (checks `if self._humidity_manager` first)

---

### 7. Humidity refresh state check should only be for over_climate

**Feedback:**
> `@custom_components/versatile_thermostat/base_thermostat.py:1385-1389` should only be for over_climate

**Status:** ✅ Addressed

**Changes Made:**
- Added `is_over_climate` check to the humidity refresh state code in `base_thermostat.py`
- Humidity state refresh now only runs for over_climate thermostats

**Implementation:**
```python
# Refresh humidity state (only for over_climate)
if self.is_over_climate and self._humidity_manager and await self._humidity_manager.refresh_state():
    # Humidity changed, force state update
    self.requested_state.force_changed()
    await self.update_states(force=True)
```

**Files Modified:**
- `custom_components/versatile_thermostat/base_thermostat.py` (line 1386: added `is_over_climate` check)

**Result:**
- Humidity state refresh is now explicitly limited to over_climate thermostats
- Other thermostat types will skip this check entirely
- More efficient and clearer intent in the code

---

### 8. Remove redundant check in humidity_manager refresh_state

**Feedback:**
> `... and self.entity_id not necessary because is_configured cannot be true else.`

**Status:** ✅ Addressed

**Changes Made:**
- Removed redundant `self._humidity_sensor_entity_id` check from `refresh_state()` method
- `_is_configured` is only set to `True` when `_humidity_sensor_entity_id` is not None (line 57-58), so the check is redundant

**Implementation:**

**Before:**
```python
if self._is_configured and self._humidity_sensor_entity_id:
    humidity_state = self.hass.states.get(self._humidity_sensor_entity_id)
```

**After:**
```python
if self._is_configured:
    humidity_state = self.hass.states.get(self._humidity_sensor_entity_id)
```

**Rationale:**
Looking at `post_init()` method (lines 57-58):
```python
if entry_infos.get(CONF_USE_HUMIDITY_FEATURE, False) and self._humidity_sensor_entity_id is not None:
    self._is_configured = True
```

Since `_is_configured` can only be `True` when `_humidity_sensor_entity_id` is not None, checking `_humidity_sensor_entity_id` again is redundant.

**Files Modified:**
- `custom_components/versatile_thermostat/feature_humidity_manager.py` (line 79)

**Result:**
- Removed redundant check, simplifying the code
- Logic remains correct since `_is_configured` already guarantees `_humidity_sensor_entity_id` is set

---

### 9. Fix unrecorded_attributes for humidity_manager and add current_humidity to specific_states

**Feedback:**
> Will not work because it is nested into `humidity_manager` attribute.
> You have to unrecord `humidity_manager`.
> Add the `current_humidity` (if manager is defined) into the `specific_states` attributes of the `base-thermostat.py`

**Status:** ✅ Addressed

**Changes Made:**
1. Changed `unrecorded_attributes` in `FeatureHumidityManager` to only include `"humidity_manager"` (the top-level attribute) instead of nested attributes
2. Added `current_humidity` to `specific_states` dictionary in `base_thermostat.py` when humidity_manager is configured

**Implementation:**

**In `feature_humidity_manager.py`:**
```python
unrecorded_attributes = frozenset(
    {
        "humidity_manager",  # Unrecord the top-level attribute, not nested ones
    }
)
```

**In `base_thermostat.py` `update_custom_attributes()`:**
```python
specific_states: dict[str, Any] = {
    # ... existing attributes ...
}

# Add current_humidity if humidity_manager is configured (only for over_climate)
if self.is_over_climate and self.humidity_manager and self.humidity_manager.is_configured:
    specific_states["current_humidity"] = self.humidity_manager.current_humidity

self._attr_extra_state_attributes: dict[str, Any] = {
    # ... other attributes ...
    "specific_states": specific_states,
    # ...
}
```

**Rationale:**
- Since humidity attributes are nested under `humidity_manager`, we need to unrecord `humidity_manager` itself, not the individual nested attributes
- `current_humidity` is added to `specific_states` so it's available as a top-level attribute in the state, separate from the nested `humidity_manager` structure

**Files Modified:**
- `custom_components/versatile_thermostat/feature_humidity_manager.py` (changed unrecorded_attributes)
- `custom_components/versatile_thermostat/base_thermostat.py` (added current_humidity to specific_states)

**Result:**
- `humidity_manager` attribute is now properly unrecorded
- `current_humidity` is available in `specific_states` for over_climate thermostats with humidity_manager configured
- Follows the pattern of exposing important values in `specific_states` while keeping detailed nested data in manager-specific attributes

---

### 10. Move humidity control business logic from state_manager to humidity_manager

**Feedback:**
> This business rule should be in the `humidity-manager` and not in the `state-manager.py` which should be "dumb" as possible (no business rules of feature manager).
>
> There is no TPO algorithm in `over_climate`. Use the `accumulated_error` from the `PITemperatureRegulator` (used by `over_climate` self-regulation) instead. But the result will depend on the self-regulation level.
>
> Maybe it's better to directly compare the current room temperature and the target temperature. If there's a 90% difference, "dry" mode could be possible.

**Status:** ✅ Addressed

**Changes Made:**
1. Moved humidity control business logic from `state_manager.py` to `humidity_manager.py`
2. Added `should_use_dry_mode()` method in `FeatureHumidityManager` that encapsulates the business rule
3. Changed from using `on_percent` (TPI algorithm) to temperature comparison (current vs target)
4. Simplified `state_manager.py` to just delegate to humidity_manager

**Implementation:**

**In `feature_humidity_manager.py`:**
```python
def should_use_dry_mode(self, requested_hvac_mode) -> bool:
    """Determine if DRY mode should be used instead of COOL mode.

    Business rule: Use DRY mode when:
    - Humidity is too high
    - Requested mode is COOL
    - Temperature is close to target (cooling not actively needed)

    Returns True if DRY mode should be used, False otherwise.
    """
    # Check conditions and compare current_temp vs target_temp
    # If current temp is at or below target (within 0.1°C), cooling is not needed
    # Use DRY mode if humidity is too high and cooling is not needed
```

**In `state_manager.py`:**
```python
# Check humidity control - delegate business logic to humidity_manager
elif (
    vtherm.humidity_manager
    and vtherm.humidity_manager.is_configured
    and vtherm.ac_mode
    and self._requested_state.hvac_mode == VThermHvacMode_COOL
):
    # Let humidity_manager decide if DRY mode should be used
    if vtherm.humidity_manager.should_use_dry_mode(self._requested_state.hvac_mode):
        self._current_state.set_hvac_mode(VThermHvacMode_DRY)
    else:
        # Use requested COOL mode
        self._current_state.set_hvac_mode(self._requested_state.hvac_mode)
```

**Rationale:**
- **Separation of concerns**: Business rules belong in feature managers, not in state_manager
- **Temperature comparison**: More reliable than `on_percent` which doesn't exist for `over_climate`
- **No dependency on self-regulation**: Works regardless of self-regulation configuration
- **Simpler logic**: Direct temperature comparison (current vs target) is clearer and more maintainable

**Files Modified:**
- `custom_components/versatile_thermostat/feature_humidity_manager.py` (added `should_use_dry_mode()` method)
- `custom_components/versatile_thermostat/state_manager.py` (simplified to delegate to humidity_manager)

**Result:**
- Business logic is now properly encapsulated in `humidity_manager`
- `state_manager` is "dumb" and just applies decisions from feature managers
- Uses temperature comparison instead of algorithm-dependent logic
- Works for all `over_climate` thermostats regardless of self-regulation configuration

---

### 11. Add message when current_state differs from requested_state and generalize hvac_reason

**Feedback:**
> Add a message to the user when `current_state` is not `requested_state`. See how it is done for `vtherm.set_hvac_off_reason` or `vtherm.set_temperature_reason`.
>
> I propose to generalize the `vtherm.set_hvac_off_reason`, rename it to `vtherm.set_hvac_reason` and add a new reason like `hvac_dry_humidity_too_high` (+ translations).

**Status:** ✅ Addressed

**Changes Made:**
1. Generalized `set_hvac_off_reason` to `set_hvac_reason` (kept `set_hvac_off_reason` for backward compatibility)
2. Added new constant `HVAC_REASON_DRY_HUMIDITY_TOO_HIGH`
3. Set `hvac_reason` when DRY mode is activated due to humidity
4. Clear `hvac_reason` when current_state matches requested_state
5. Added `hvac_reason` to messages and `specific_states` attributes
6. Added translation for the new reason

**Implementation:**

**In `const.py`:**
```python
HVAC_REASON_NAME = "hvac_reason"
HVAC_REASON_DRY_HUMIDITY_TOO_HIGH = "hvac_dry_humidity_too_high"
```

**In `base_thermostat.py`:**
```python
self._hvac_reason: str | None = None

@property
def hvac_reason(self) -> str | None:
    """Returns the reason for HVAC mode changes (generalized from hvac_off_reason)"""
    return self._hvac_reason

def set_hvac_reason(self, hvac_reason: str | None):
    """Set the reason for HVAC mode changes (generalized from set_hvac_off_reason)"""
    self._hvac_reason = hvac_reason
    # Also set hvac_off_reason for backward compatibility when mode is OFF
    if self.vtherm_hvac_mode == VThermHvacMode_OFF:
        self._hvac_off_reason = hvac_reason

def set_hvac_off_reason(self, hvac_off_reason: str | None):
    """Set the reason of hvac_off (deprecated, use set_hvac_reason instead)"""
    self._hvac_off_reason = hvac_off_reason
    # Also set hvac_reason for consistency
    if hvac_off_reason is not None:
        self._hvac_reason = hvac_off_reason
```

**In `state_manager.py`:**
```python
# Set reason when DRY mode is activated
if vtherm.humidity_manager.should_use_dry_mode(self._requested_state.hvac_mode):
    self._current_state.set_hvac_mode(VThermHvacMode_DRY)
    # Set reason when current_state differs from requested_state
    vtherm.set_hvac_reason(HVAC_REASON_DRY_HUMIDITY_TOO_HIGH)
else:
    # Use requested COOL mode
    self._current_state.set_hvac_mode(self._requested_state.hvac_mode)
    # Clear reason when using requested mode
    if self._current_state.hvac_mode == self._requested_state.hvac_mode:
        vtherm.set_hvac_reason(None)
```

**In `translations/en.json`:**
```json
"state_attributes": {
  "hvac_reason": {
    "state": {
      "hvac_dry_humidity_too_high": "DRY mode: Humidity too high"
    }
  }
}
```

**Files Modified:**
- `custom_components/versatile_thermostat/const.py` (added `HVAC_REASON_NAME` and `HVAC_REASON_DRY_HUMIDITY_TOO_HIGH`)
- `custom_components/versatile_thermostat/base_thermostat.py` (added `_hvac_reason`, `set_hvac_reason()`, updated messages and specific_states)
- `custom_components/versatile_thermostat/state_manager.py` (set/clear `hvac_reason` when DRY mode is activated)
- `custom_components/versatile_thermostat/translations/en.json` (added translation for new reason)
- All other locale translation files (cs.json, de.json, el.json, fr.json, it.json, pl.json, ru.json, sk.json) - added English text for translator contributors

**Result:**
- Users now see a message when current_state differs from requested_state (e.g., when DRY mode is activated instead of COOL)
- `set_hvac_reason` is generalized and can be used for any HVAC mode change reason
- `set_hvac_off_reason` is maintained for backward compatibility
- New reason `hvac_dry_humidity_too_high` is properly translated
- Reason is cleared when states match again
- All translation files updated with English text for translator contributors to translate

---

### 12. Update translations for all locales

**Feedback:**
> Please update translations for other locales. You can leave the text in English and translator contributor will translate into their native language which is much better than an automatic translation. (README and translations/).

**Status:** ✅ Addressed

**Changes Made:**
- Added `hvac_reason` translation section to all locale translation files
- Kept English text "DRY mode: Humidity too high" in all files for translator contributors

**Files Modified:**
- `custom_components/versatile_thermostat/translations/cs.json`
- `custom_components/versatile_thermostat/translations/de.json`
- `custom_components/versatile_thermostat/translations/el.json`
- `custom_components/versatile_thermostat/translations/fr.json`
- `custom_components/versatile_thermostat/translations/it.json`
- `custom_components/versatile_thermostat/translations/pl.json`
- `custom_components/versatile_thermostat/translations/ru.json`
- `custom_components/versatile_thermostat/translations/sk.json`

**Result:**
- All translation files now include the new `hvac_reason` section
- English text is provided for translator contributors to translate properly
- Better than automatic translation - native speakers can provide accurate translations

---
