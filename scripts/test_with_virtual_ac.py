#!/usr/bin/env python3
"""
Test script for Virtual AC integration with Versatile Thermostat.

This script demonstrates how to:
1. Check for Virtual AC device (prompts for manual creation if not found)
2. Check for Versatile Thermostat (prompts for manual creation if not found)
3. Check for required sensors (prompts for manual creation if not found)
4. Run various test scenarios
5. Clean up test entities

The script uses a check-and-prompt approach: it verifies that required entities exist,
and if they don't, it provides detailed instructions and waits for the user to create
them manually. This is more reliable than trying to create entities programmatically
via the Home Assistant REST API.

Requirements:
    pip install aiohttp

Usage:
    # Using command-line arguments
    # Virtual AC only tests
    python test_with_virtual_ac.py --url http://homeassistant.local:8123 --token YOUR_TOKEN --test-type virtual-ac-only

    # Integrated tests (Virtual AC + Versatile Thermostat)
    python test_with_virtual_ac.py --url http://homeassistant.local:8123 --token YOUR_TOKEN --test-type integrated

    # With custom sensors
    python test_with_virtual_ac.py --url http://homeassistant.local:8123 --token YOUR_TOKEN \
        --temp-sensor sensor.my_temp --humidity-sensor sensor.my_humidity

    # Cleanup after tests
    python test_with_virtual_ac.py --url http://homeassistant.local:8123 --token YOUR_TOKEN --cleanup

    # Using environment variables (recommended)
    export HASS_URL="http://homeassistant.local:8123"
    export HASS_TOKEN="YOUR_TOKEN"
    export HASS_MODE="instant"
    export HASS_TEST_TYPE="integrated"
    export HASS_CLEANUP="true"
    python test_with_virtual_ac.py

    # Or mix and match (env vars override defaults, CLI args override env vars)
    export HASS_URL="http://homeassistant.local:8123"
    export HASS_TOKEN="YOUR_TOKEN"
    python test_with_virtual_ac.py --test-type virtual-ac-only --mode fast-realistic

Prerequisites for Integrated Tests:
    - Virtual AC integration installed and working
    - Versatile Thermostat integration installed

    SETUP APPROACH:
    The script uses a check-and-prompt approach:
    1. Checks if Virtual AC exists (climate.test_virtual_ac by default)
       - If not found, provides instructions and waits for you to create it
    2. Checks if required sensors exist
       - Prefers Virtual AC's native sensors (sensor.test_virtual_ac_indoor_temperature, etc.)
       - Falls back to input_number entities if Virtual AC doesn't create sensors
       - If sensors don't exist, provides instructions and waits for you to create them
    3. Checks if Versatile Thermostat exists (climate.test_versatile_thermostat by default)
       - If not found, provides detailed configuration instructions and waits for you to create it

    The script will pause at each step and wait for you to press ENTER after creating
    the required entity. This ensures all entities are properly configured before tests run.

=============================================================================
VIRTUAL AC API REFERENCE GUIDE
=============================================================================

1. CREATING A VIRTUAL AC DEVICE
   -----------------------------

   Endpoint: POST /api/config/config_entries/flow

   Request Body:
   {
       "handler": "virtual_ac",
       "show_advanced_options": true,
       "user_input": {
           # Basic Configuration (Required)
           "name": "test_ac_001",                    # Device name (required)
           "initial_temp": 22.0,                    # Starting indoor temp (°C)
           "initial_humidity": 50.0,                # Starting indoor humidity (%)
           "ambient_temp": 25.0,                    # Outdoor/ambient temp (°C)
           "ambient_humidity": 60.0,                # Outdoor/ambient humidity (%)

           # Basic Configuration (Optional)
           "temp_unit": "celsius",                  # "celsius" or "fahrenheit"
           "min_temp": 16.0,                        # Minimum temperature
           "max_temp": 30.0,                        # Maximum temperature
           "precision": 0.5,                         # Temperature step/precision

           # Advanced Configuration (Optional)
           "simulation_mode": "instant",            # "instant" or "realistic"
           "cooling_rate": 0.5,                     # °C per minute (realistic mode)
           "heating_rate": 0.5,                     # °C per minute (realistic mode)
           "dry_humidity_rate": 2.0,                # % per minute (realistic mode)
           "ambient_drift_rate": 0.1,               # °C per minute when OFF
           "update_interval": 10                    # Seconds between updates
       }
   }

   Response: {
       "flow_id": "...",
       "type": "create_entry",
       "entry_id": "..."
   }

   Note: You need to complete the flow by calling the flow completion endpoint
   with the flow_id returned from this call.


2. VIRTUAL AC SERVICES
   --------------------

   All services use: POST /api/services/{domain}/{service}

   A. virtual_ac.set_state
      ----------------
      Set current temperature and/or humidity values directly.

      Service Data:
      {
          "entity_id": "climate.test_ac",           # Required: Virtual AC entity
          "current_temperature": 25.0,             # Optional: Indoor temp (°C)
          "current_humidity": 60.0,                # Optional: Indoor humidity (%)
          "external_temperature": 30.0,           # Optional: Outdoor temp (°C)
          "external_humidity": 70.0                # Optional: Outdoor humidity (%)
      }

      Example:
      POST /api/services/virtual_ac/set_state
      {
          "entity_id": "climate.test_ac",
          "current_temperature": 25.0,
          "current_humidity": 60.0
      }

      Use Cases:
      - Set initial conditions before starting simulation
      - Reset state for test scenarios
      - Simulate specific conditions


   B. virtual_ac.sync_from_entities
      ---------------------------
      Sync temperature/humidity from real climate or weather entities.

      Service Data (YAML format):
      {
          "entity_id": "climate.test_ac",           # Required: Virtual AC entity
          "climate_entity": "climate.real_ac",      # Optional: Source climate entity
          "weather_entity": "weather.home"          # Optional: Source weather entity
      }

      Service Data (with target selector):
      {
          "target": {
              "entity_id": "climate.test_ac"
          },
          "climate_entity": "climate.real_ac",
          "weather_entity": "weather.home"
      }

      Example:
      POST /api/services/virtual_ac/sync_from_entities
      {
          "entity_id": "climate.test_ac",
          "climate_entity": "climate.living_room_thermostat",
          "weather_entity": "weather.home"
      }

      Behavior:
      - Reads current_temperature and current_humidity from climate_entity
      - Reads temperature and humidity from weather_entity
      - Updates Virtual AC with these values

      Use Cases:
      - Initialize Virtual AC to match real conditions
      - Sync outdoor conditions from weather
      - Match indoor conditions from real thermostat


3. STANDARD CLIMATE SERVICES
   --------------------------

   Virtual AC supports all standard Home Assistant climate services.

   A. climate.set_temperature
      ----------------------
      Set target temperature.

      Service Data:
      {
          "entity_id": "climate.test_ac",           # Required
          "temperature": 22.0                       # Target temperature (°C)
      }

      Example:
      POST /api/services/climate/set_temperature
      {
          "entity_id": "climate.test_ac",
          "temperature": 22.0
      }


   B. climate.set_hvac_mode
      ---------------------
      Change HVAC mode.

      Service Data:
      {
          "entity_id": "climate.test_ac",           # Required
          "hvac_mode": "cool"                       # Mode: "off", "cool", "heat",
                                                     #        "dry", "fan_only", "auto"
      }

      Example:
      POST /api/services/climate/set_hvac_mode
      {
          "entity_id": "climate.test_ac",
          "hvac_mode": "cool"
      }

      Available Modes:
      - "off": AC off, drifts toward ambient
      - "cool": Cooling mode, decreases temperature
      - "heat": Heating mode, increases temperature
      - "dry": Dehumidification mode, reduces humidity
      - "fan_only": Fan only, no temp/humidity change
      - "auto": Automatically switches between heat/cool


   C. climate.set_fan_mode
      --------------------
      Set fan speed.

      Service Data:
      {
          "entity_id": "climate.test_ac",           # Required
          "fan_mode": "high"                        # "auto", "low", "medium", "high"
      }

      Example:
      POST /api/services/climate/set_fan_mode
      {
          "entity_id": "climate.test_ac",
          "fan_mode": "high"
      }


   D. climate.set_swing_mode
      ---------------------
      Set swing mode.

      Service Data:
      {
          "entity_id": "climate.test_ac",           # Required
          "swing_mode": "on"                        # "off" or "on"
      }

      Example:
      POST /api/services/climate/set_swing_mode
      {
          "entity_id": "climate.test_ac",
          "swing_mode": "on"
      }


   E. climate.set_preset_mode
      ----------------------
      Set preset mode.

      Service Data:
      {
          "entity_id": "climate.test_ac",           # Required
          "preset_mode": "eco"                      # "eco", "comfort", "sleep", "away"
      }

      Example:
      POST /api/services/climate/set_preset_mode
      {
          "entity_id": "climate.test_ac",
          "preset_mode": "eco"
      }

      Note: Preset modes adjust target temperature:
      - "eco": Target - 2°C
      - "comfort": Normal target
      - "sleep": Target - 1°C
      - "away": Target - 3°C


4. READING STATE
   -------------

   Endpoint: GET /api/states/{entity_id}

   Example:
   GET /api/states/climate.test_ac

   Response:
   {
       "entity_id": "climate.test_ac",
       "state": "cool",                             # Current HVAC mode
       "attributes": {
           "current_temperature": 22.5,            # Current indoor temp
           "temperature": 22.0,                    # Target temperature
           "current_humidity": 50.0,               # Current indoor humidity
           "humidity": 50.0,                       # Target humidity (same as current)
           "hvac_modes": ["off", "cool", "heat", "dry", "fan_only", "auto"],
           "fan_mode": "auto",                     # Current fan mode
           "fan_modes": ["auto", "low", "medium", "high"],
           "swing_mode": "off",                    # Current swing mode
           "swing_modes": ["off", "on"],
           "preset_mode": "comfort",               # Current preset
           "preset_modes": ["eco", "comfort", "sleep", "away"],
           "min_temp": 16.0,
           "max_temp": 30.0,
           "target_temp_step": 0.5,
           "simulation_mode": "realistic",         # Current simulation mode
           "cooling_rate": 0.5,                    # Configured cooling rate
           "heating_rate": 0.5,                    # Configured heating rate
           "ambient_temperature": 25.0,            # Outdoor/ambient temp
           "temperature_difference": -0.5,        # current - target
           "supported_features": 57,               # Bitmask of supported features
           "friendly_name": "test ac"              # Device friendly name
       },
       "last_changed": "2025-12-20T15:30:00.000Z",
       "last_updated": "2025-12-20T15:30:00.000Z"
   }


5. CONFIGURATION OPTIONS
   ----------------------

   To update configuration options after creation:

   Endpoint: POST /api/config/config_entries/entry/{entry_id}/options

   Request Body:
   {
       "simulation_mode": "realistic",
       "cooling_rate": 2.0,
       "heating_rate": 2.0,
       "dry_humidity_rate": 5.0,
       "ambient_drift_rate": 0.5,
       "update_interval": 5
   }

   Or use the options flow:
   Endpoint: POST /api/config/config_entries/options/flow
   {
       "handler": "virtual_ac",
       "entry_id": "...",
       "user_input": {
           "simulation_mode": "realistic",
           "cooling_rate": 2.0,
           ...
       }
   }


6. DELETING A DEVICE
   ------------------

   Endpoint: DELETE /api/config/config_entries/entry/{entry_id}

   Example:
   DELETE /api/config/config_entries/entry/abc123...

   This removes the Virtual AC device and all associated entities.


7. SIMULATION MODES EXPLAINED
   ---------------------------

   A. Instant Mode
      ------------
      - All changes happen immediately
      - Temperature instantly reaches target (respects mode direction)
      - Humidity changes immediately
      - No time-based simulation
      - Best for: Unit tests, UI tests, quick validation

      Configuration:
      {
          "simulation_mode": "instant"
      }


   B. Realistic Mode (Standard)
      -------------------------
      - Gradual changes over time
      - Temperature changes at configured rate
      - Humidity changes gradually
      - Updates every update_interval seconds
      - Best for: Integration tests, realistic behavior validation

      Configuration:
      {
          "simulation_mode": "realistic",
          "cooling_rate": 0.5,        # °C per minute
          "heating_rate": 0.5,        # °C per minute
          "dry_humidity_rate": 2.0,    # % per minute
          "ambient_drift_rate": 0.1,  # °C per minute
          "update_interval": 10       # seconds
      }


   C. Realistic Mode (Fast - Recommended for Testing)
      -----------------------------------------------
      - Same as realistic but faster
      - 2-5x faster rates for quicker test completion
      - Still realistic behavior, just accelerated
      - Best for: Complex scenarios, mode transitions

      Configuration:
      {
          "simulation_mode": "realistic",
          "cooling_rate": 2.0,        # 4x faster
          "heating_rate": 2.0,        # 4x faster
          "dry_humidity_rate": 5.0,    # 2.5x faster
          "ambient_drift_rate": 0.5,  # 5x faster
          "update_interval": 5        # 2x faster
      }


8. HVAC MODE BEHAVIOR
   ------------------

   OFF:
   - Temperature drifts toward ambient_temp at ambient_drift_rate
   - Humidity drifts toward ambient_humidity at ~30% of dry_humidity_rate
   - No active cooling/heating

   COOL:
   - Temperature decreases toward target at cooling_rate
   - Humidity decreases slightly (~1%/min)
   - Only decreases temperature (won't heat)

   HEAT:
   - Temperature increases toward target at heating_rate
   - Humidity decreases slightly (~0.5%/min)
   - Only increases temperature (won't cool)

   DRY:
   - Temperature decreases slightly (~1°C)
   - Humidity decreases significantly at dry_humidity_rate
   - Primary focus on dehumidification

   FAN_ONLY:
   - No temperature change
   - No humidity change
   - Air circulation only

   AUTO:
   - Automatically switches between HEAT and COOL
   - Uses HEAT if current_temp < target_temp
   - Uses COOL if current_temp > target_temp
   - Maintains current mode if within tolerance


9. TESTING BEST PRACTICES
   ----------------------

   A. Simple Tests (Use Instant Mode)
      - Set simulation_mode: "instant"
      - Test mode switching
      - Test temperature setpoints
      - Test fan/swing controls
      - Fast execution, deterministic results

   B. Integration Tests (Use Fast Realistic Mode)
      - Set simulation_mode: "realistic" with fast rates
      - Test temperature ramps
      - Test mode transitions (cool → dry)
      - Test hysteresis behavior
      - Realistic but accelerated

   C. Complex Scenarios
      - Use fast realistic mode
      - Set initial conditions with set_state
      - Monitor state changes over time
      - Test Versatile Thermostat integration
      - Validate transitions and timing

   D. Cleanup
      - Always delete test devices after tests
      - Use random names to avoid conflicts
      - Remove associated entities (sensors, selects)


10. EXAMPLE TEST FLOW
    ------------------

    # 1. Create Virtual AC
    POST /api/config/config_entries/flow
    {
        "handler": "virtual_ac",
        "user_input": {
            "name": "test_ac_001",
            "simulation_mode": "instant",
            ...
        }
    }

    # 2. Set initial conditions
    POST /api/services/virtual_ac/set_state
    {
        "entity_id": "climate.test_ac_001",
        "current_temperature": 25.0,
        "current_humidity": 60.0
    }

    # 3. Set target temperature
    POST /api/services/climate/set_temperature
    {
        "entity_id": "climate.test_ac_001",
        "temperature": 22.0
    }

    # 4. Set HVAC mode
    POST /api/services/climate/set_hvac_mode
    {
        "entity_id": "climate.test_ac_001",
        "hvac_mode": "cool"
    }

    # 5. Monitor state
    GET /api/states/climate.test_ac_001

    # 6. Cleanup
    DELETE /api/config/config_entries/entry/{entry_id}


11. ERROR HANDLING
    ---------------

    Common Errors:

    - 404: Entity not found
      → Check entity_id spelling
      → Wait for device to be created (may take a few seconds)

    - 400: Invalid service data
      → Check required fields are present
      → Verify data types (float for temps, string for modes)

    - 500: Internal server error
      → Check Home Assistant logs
      → Verify integration is loaded
      → Check for configuration errors

    Always check response status codes and handle errors appropriately.


12. RATE CALCULATIONS
    -----------------

    Temperature Change Time:
    time_minutes = abs(current_temp - target_temp) / rate

    Example:
    - Current: 25°C, Target: 20°C, Rate: 2.0°C/min
    - Time = (25 - 20) / 2.0 = 2.5 minutes

    Humidity Change Time:
    time_minutes = abs(current_humidity - target_humidity) / rate

    Example:
    - Current: 70%, Target: 50%, Rate: 5.0%/min
    - Time = (70 - 50) / 5.0 = 4.0 minutes

    Update Frequency:
    - State updates every update_interval seconds
    - In realistic mode, check state at least every update_interval
    - For fast tests, use update_interval: 5 seconds

=============================================================================
END OF API REFERENCE
=============================================================================
"""

import argparse
import asyncio
import json
import os
import random
import string
import time
from typing import Any, Dict, Optional

import aiohttp


class HomeAssistantAPI:
    """Client for Home Assistant REST API."""

    def __init__(self, url: str, token: str):
        """Initialize API client."""
        self.url = url.rstrip("/")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def call_service(
        self, domain: str, service: str, service_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call a Home Assistant service."""
        url = f"{self.url}/api/services/{domain}/{service}"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=self.headers, json=service_data or {}
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_state(self, entity_id: str) -> Dict[str, Any]:
        """Get state of an entity."""
        url = f"{self.url}/api/states/{entity_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                return await response.json()

    async def get_states(self) -> list[Dict[str, Any]]:
        """Get all states."""
        url = f"{self.url}/api/states"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                return await response.json()

    async def create_config_entry(
        self, domain: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a config entry (integration)."""
        url = f"{self.url}/api/config/config_entries/flow"
        payload = {
            "handler": domain,
            "show_advanced_options": True,
            "user_input": data,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=self.headers, json=payload
            ) as response:
                if response.status == 200:
                    flow_result = await response.json()
                    flow_id = flow_result.get("flow_id")
                    flow_type = flow_result.get("type")

                    if not flow_id:
                        error_text = await response.text()
                        raise Exception(f"Failed to get flow_id from response: {flow_result}")

                    # Check if flow needs completion or is already done
                    if flow_type == "create_entry":
                        # Flow is already complete
                        return flow_result

                    # This function is deprecated - Virtual AC now uses step-by-step flow completion
                    # Keeping for backward compatibility but should use create_virtual_ac instead
                    raise Exception("This method is deprecated. Use step-by-step flow completion.")
                else:
                    error_text = await response.text()
                    try:
                        error_json = await response.json()
                        error_msg = error_json.get("message", error_text)
                    except:
                        error_msg = error_text
                    raise Exception(f"Failed to create config entry (status {response.status}): {error_msg}")

    async def delete_config_entry(self, entry_id: str) -> None:
        """Delete a config entry."""
        url = f"{self.url}/api/config/config_entries/entry/{entry_id}"
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=self.headers) as response:
                response.raise_for_status()

    async def wait_for_state(
        self,
        entity_id: str,
        attribute: str,
        expected_value: Any,
        timeout: int = 60,
        check_interval: float = 1.0,
    ) -> bool:
        """Wait for an entity attribute to reach expected value."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            state = await self.get_state(entity_id)
            current_value = state.get("attributes", {}).get(attribute)
            if current_value == expected_value:
                return True
            await asyncio.sleep(check_interval)
        return False

    async def wait_for_state_change(
        self,
        entity_id: str,
        timeout: int = 60,
        check_interval: float = 1.0,
    ) -> Dict[str, Any]:
        """Wait for any state change on an entity."""
        initial_state = await self.get_state(entity_id)
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_state = await self.get_state(entity_id)
            if current_state != initial_state:
                return current_state
            await asyncio.sleep(check_interval)
        raise TimeoutError(f"State did not change for {entity_id} within {timeout}s")


def generate_random_name(prefix: str = "test_ac") -> str:
    """Generate a random device name."""
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}_{random_suffix}"


async def check_entity_exists(
    api: HomeAssistantAPI,
    entity_id: str,
    entity_type: str,
    creation_instructions: str,
) -> Dict[str, Any]:
    """
    Check if an entity exists. If not, provide instructions and wait for user to create it.

    Args:
        api: Home Assistant API client
        entity_id: Expected entity ID (e.g., "climate.test_virtual_ac")
        entity_type: Human-readable type (e.g., "Virtual AC", "Versatile Thermostat")
        creation_instructions: Detailed instructions for creating the entity

    Returns:
        Entity state dictionary

    Raises:
        Exception: If entity doesn't exist after user confirmation
    """
    print(f"\n🔍 Checking for {entity_type}: {entity_id}")

    # First check
    try:
        state = await api.get_state(entity_id)
        print(f"  ✅ Found {entity_type}: {entity_id}")
        return state
    except Exception:
        pass

    # Entity doesn't exist - provide instructions
    print(f"\n  ❌ {entity_type} '{entity_id}' not found.")
    print("\n" + "=" * 70)
    print(f"📋 INSTRUCTIONS: Create {entity_type}")
    print("=" * 70)
    print(creation_instructions)
    print("=" * 70)
    print("\n⏸️  Press ENTER after you have created the entity...")

    # Wait for user input
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        raise Exception(f"User cancelled. Please create {entity_type} '{entity_id}' and run the script again.")

    # Check again after user confirmation
    print(f"\n🔍 Verifying {entity_type} was created...")
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            state = await api.get_state(entity_id)
            print(f"  ✅ Found {entity_type}: {entity_id}")
            return state
        except Exception:
            if attempt < max_retries:
                print(f"  ⏳ Waiting... (attempt {attempt}/{max_retries})")
                await asyncio.sleep(2)
            else:
                raise Exception(
                    f"{entity_type} '{entity_id}' still not found after {max_retries} attempts. "
                    f"Please verify it was created correctly and run the script again."
                )

    # Should never reach here, but just in case
    raise Exception(f"Failed to verify {entity_type} '{entity_id}'")


async def sync_virtual_ac_to_sensors(
    api: HomeAssistantAPI,
    virtual_ac_entity_id: str,
    temp_sensor_entity_id: str,
    humidity_sensor_entity_id: str = None,
    verbose: bool = True,
) -> None:
    """Sync Virtual AC state to input_number sensors.

    This automatically reads current_temperature and current_humidity from Virtual AC
    and updates the corresponding input_number sensors. This ensures Versatile Thermostat
    always sees the current Virtual AC state.

    Note: Only syncs if sensors are input_number entities. If Virtual AC creates its own
    sensor entities, they're already in sync automatically.
    """
    # Only sync if we're using input_number entities
    if not temp_sensor_entity_id.startswith("input_number."):
        if verbose:
            print(f"  ℹ️  Temperature sensor {temp_sensor_entity_id} is not an input_number, skipping sync (already in sync)")
        return

    # Get Virtual AC state
    ac_state = await api.get_state(virtual_ac_entity_id)
    attrs = ac_state.get("attributes", {})
    current_temp = attrs.get("current_temperature")
    current_humidity = attrs.get("current_humidity")

    # Update temperature sensor
    if current_temp is not None:
        try:
            await api.call_service(
                "input_number",
                "set_value",
                {"entity_id": temp_sensor_entity_id, "value": current_temp},
            )
            if verbose:
                print(f"  ✅ Synced temp: {current_temp}°C → {temp_sensor_entity_id}")
        except Exception as e:
            if verbose:
                print(f"  ⚠️  Could not sync temp to {temp_sensor_entity_id}: {e}")
            raise

    # Update humidity sensor (only if it's an input_number)
    if current_humidity is not None and humidity_sensor_entity_id:
        if humidity_sensor_entity_id.startswith("input_number."):
            try:
                await api.call_service(
                    "input_number",
                    "set_value",
                    {"entity_id": humidity_sensor_entity_id, "value": current_humidity},
                )
                if verbose:
                    print(f"  ✅ Synced humidity: {current_humidity}% → {humidity_sensor_entity_id}")
            except Exception as e:
                if verbose:
                    print(f"  ⚠️  Could not sync humidity to {humidity_sensor_entity_id}: {e}")
                raise
        elif verbose:
            print(f"  ℹ️  Humidity sensor {humidity_sensor_entity_id} is not an input_number, skipping sync (already in sync)")


def get_virtual_ac_instructions(name: str, instant_mode: bool = True, fast_realistic: bool = False) -> str:
    """Generate instructions for creating a Virtual AC device.

    Note: instant_mode=True is recommended for testing because:
    - Tests run faster (no waiting for temperature ramps)
    - Results are deterministic and immediate
    - Better for CI/CD and automated testing
    - No timing-related flakiness

    Use realistic mode only if you specifically need to test timing behavior.
    """
    mode_desc = "instant" if instant_mode else ("fast realistic" if fast_realistic else "realistic")

    instructions = f"""
To create the Virtual AC device '{name}':

1. Open Home Assistant UI
2. Go to Settings → Devices & Services → Add Integration
3. Search for "Virtual AC" and select it
4. Configure with these settings:

   BASIC SETTINGS:
   - Name: {name}
   - Initial Temperature: 22.0°C
   - Initial Humidity: 50.0%
   - Ambient Temperature: 25.0°C
   - Ambient Humidity: 60.0%
   - Temperature Unit: Celsius
   - Min Temperature: 16.0°C
   - Max Temperature: 30.0°C
   - Precision: 0.5°C

   ADVANCED SETTINGS (click "Show advanced options"):
   - Simulation Mode: {mode_desc}"""

    if not instant_mode:
        if fast_realistic:
            instructions += """
   - Cooling Rate: 2.0
   - Heating Rate: 2.0
   - Dry Humidity Rate: 5.0
   - Ambient Drift Rate: 0.5
   - Update Interval: 5 seconds"""
        else:
            instructions += """
   - Cooling Rate: 0.5
   - Heating Rate: 0.5
   - Dry Humidity Rate: 2.0
   - Ambient Drift Rate: 0.1
   - Update Interval: 10 seconds"""

    instructions += f"""

5. Complete the configuration
6. Verify the entity is created: climate.{name}

Expected entity ID: climate.{name}
"""
    return instructions


async def check_virtual_ac_exists(
    api: HomeAssistantAPI,
    name: str,
    instant_mode: bool = True,
    fast_realistic: bool = False,
) -> Dict[str, Any]:
    """Check if Virtual AC exists, prompt for creation if not."""
    entity_id = f"climate.{name}"
    instructions = get_virtual_ac_instructions(name, instant_mode, fast_realistic)

    state = await check_entity_exists(api, entity_id, "Virtual AC", instructions)

    # Verify entity details
    print(f"\n✅ Virtual AC entity verified:")
    print(f"   Entity ID: {entity_id}")
    print(f"   State: {state.get('state')}")
    attrs = state.get("attributes", {})
    print(f"   Current Temperature: {attrs.get('current_temperature')}°C")
    print(f"   Current Humidity: {attrs.get('current_humidity')}%")
    print(f"   Target Temperature: {attrs.get('temperature')}°C")
    print(f"   HVAC Modes: {attrs.get('hvac_modes', [])}")

    return {
        "entity_id": entity_id,
        "state": state,
    }


async def create_virtual_ac(
    api: HomeAssistantAPI,
    name: str,
    instant_mode: bool = True,
    fast_realistic: bool = False,
) -> Dict[str, Any]:
    """Check if Virtual AC exists, prompt for creation if not."""
    return await check_virtual_ac_exists(api, name, instant_mode, fast_realistic)

    # Basic configuration (for "user" step)
    basic_config = {
        "name": name,
        "initial_temp": 22.0,
        "initial_humidity": 50.0,
        "ambient_temp": 25.0,
        "ambient_humidity": 60.0,
        "temp_unit": "celsius",
        "min_temp": 16.0,
        "max_temp": 30.0,
        "precision": 0.5,
    }

    # Advanced configuration (for "advanced" step)
    advanced_config = {}
    if instant_mode:
        advanced_config["simulation_mode"] = "instant"
    else:
        advanced_config["simulation_mode"] = "realistic"
        if fast_realistic:
            # Fast realistic mode for quicker tests
            advanced_config["cooling_rate"] = 2.0
            advanced_config["heating_rate"] = 2.0
            advanced_config["dry_humidity_rate"] = 5.0
            advanced_config["ambient_drift_rate"] = 0.5
            advanced_config["update_interval"] = 5
        else:
            # Standard realistic mode
            advanced_config["cooling_rate"] = 0.5
            advanced_config["heating_rate"] = 0.5
            advanced_config["dry_humidity_rate"] = 2.0
            advanced_config["ambient_drift_rate"] = 0.1
            advanced_config["update_interval"] = 10

    try:
        # Step 1: Start the flow
        print("  📝 Step 1: Starting Virtual AC config flow...")
        url = f"{api.url}/api/config/config_entries/flow"
        payload = {
            "handler": "virtual_ac",
            "show_advanced_options": True,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=api.headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to start flow: {error_text}")
                flow_result = await response.json()
                flow_id = flow_result.get("flow_id")
                if not flow_id:
                    raise Exception(f"No flow_id in response: {flow_result}")
                print(f"  ✅ Flow started: {flow_id}")

            # Step 2: Complete "user" step with basic config
            print("  📝 Step 2: Completing basic configuration...")
            current_step_id = flow_result.get("step_id", "user")
            flow_result = await complete_flow_step(api, flow_id, current_step_id, basic_config)
            # Update flow_id if returned
            if "flow_id" in flow_result:
                flow_id = flow_result["flow_id"]
            print(f"  ✅ Basic configuration complete. Flow type: {flow_result.get('type')}, step_id: {flow_result.get('step_id')}")

            # Step 3: Complete "advanced" step (if present)
            entry_id = flow_result.get("entry_id")
            if not entry_id and flow_result.get("type") == "form":
                current_step_id = flow_result.get("step_id")
                if current_step_id == "advanced":
                    print("  📝 Step 3: Completing advanced configuration...")
                    flow_result = await complete_flow_step(api, flow_id, "advanced", advanced_config)
                    if "flow_id" in flow_result:
                        flow_id = flow_result["flow_id"]

                    # Extract entry_id from various possible locations
                    entry_id = (
                        flow_result.get("entry_id") or
                        flow_result.get("result", {}).get("entry_id") or
                        (flow_result.get("result") if isinstance(flow_result.get("result"), str) else None)
                    )
                    print(f"  ✅ Advanced configuration complete. Flow type: {flow_result.get('type')}, entry_id: {entry_id}")

            # Final check for entry_id
            if not entry_id:
                # Try extracting from result if it's a create_entry type
                if flow_result.get("type") == "create_entry":
                    entry_id = (
                        flow_result.get("entry_id") or
                        flow_result.get("result", {}).get("entry_id") or
                        (flow_result.get("result") if isinstance(flow_result.get("result"), str) else None)
                    )

            if entry_id:
                print(f"✅ Virtual AC created with entry_id: {entry_id}")
            else:
                print(f"⚠️  No entry_id in final result. Flow type: {flow_result.get('type')}, step_id: {flow_result.get('step_id')}")
                # Don't fail yet - entity might still be created

        # Wait for entity to be available and verify it exists
        entity_id = f"climate.{name.lower().replace(' ', '_')}"
        print(f"⏳ Waiting for entity: {entity_id}")

        # Retry checking for entity (up to 10 seconds)
        max_retries = 10
        retry_count = 0
        state = None

        while retry_count < max_retries:
            try:
                state = await api.get_state(entity_id)
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(1)
                else:
                    # Last attempt failed - try searching for entities with similar names
                    print(f"  ⚠️  Entity {entity_id} not found. Searching for similar entities...")
                    try:
                        all_states = await api.get_states()
                        climate_entities = [s for s in all_states if s.get("entity_id", "").startswith("climate.") and name.lower() in s.get("entity_id", "").lower()]
                        if climate_entities:
                            print(f"  Found similar entities: {[e.get('entity_id') for e in climate_entities]}")
                            # Try the first one
                            entity_id = climate_entities[0].get("entity_id")
                            state = climate_entities[0]
                            print(f"  ✅ Using found entity: {entity_id}")
                            break
                    except Exception as search_error:
                        print(f"  ⚠️  Could not search for entities: {search_error}")

        if state:
            attrs = state.get("attributes", {})
            print(f"✅ Virtual AC entity verified:")
            print(f"   Entity ID: {entity_id}")
            print(f"   State: {state.get('state')}")
            print(f"   Current Temperature: {attrs.get('current_temperature')}°C")
            print(f"   Current Humidity: {attrs.get('current_humidity')}%")
            print(f"   Target Temperature: {attrs.get('temperature')}°C")
            print(f"   HVAC Modes: {attrs.get('hvac_modes')}")
            return {"entry_id": entry_id, "entity_id": entity_id, "name": name}
        else:
            error_msg = f"Virtual AC entity {entity_id} not found after {max_retries} seconds."
            if entry_id:
                error_msg += f" Entry ID: {entry_id}"
            else:
                error_msg += f" No entry_id returned from flow completion."
            raise Exception(error_msg)

    except Exception as e:
        print(f"❌ Failed to create Virtual AC: {e}")
        raise


async def configure_virtual_ac(
    api: HomeAssistantAPI, entity_id: str, **options
) -> None:
    """Configure Virtual AC options."""
    print(f"\n⚙️  Configuring {entity_id}")

    # Get config entry ID from entity
    state = await api.get_state(entity_id)
    # Note: We'd need to get this from the entity registry
    # For now, we'll use the service to update options

    # Update via service if needed
    # This is a simplified version - full implementation would use config entry options flow


async def get_flow_state(api: HomeAssistantAPI, flow_id: str) -> Dict[str, Any]:
    """Get the current state of a config flow."""
    url = f"{api.url}/api/config/config_entries/flow/{flow_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=api.headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get flow state: {error_text}")
            return await response.json()


async def create_versatile_thermostat_flow(
    api: HomeAssistantAPI, name: str
) -> Dict[str, Any]:
    """Start a Versatile Thermostat config flow."""
    url = f"{api.url}/api/config/config_entries/flow"
    payload = {
        "handler": "versatile_thermostat",
        "show_advanced_options": True,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=api.headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                try:
                    error_json = await response.json()
                    error_msg = error_json.get("message", error_text)
                except:
                    error_msg = error_text
                raise Exception(f"Failed to create flow: {error_msg}")
            result = await response.json()
            # Check what step we're on
            if "flow_id" in result:
                flow_state = await get_flow_state(api, result["flow_id"])
                print(f"  Flow state: type={flow_state.get('type')}, step_id={flow_state.get('step_id')}")
            return result


async def complete_flow_step(
    api: HomeAssistantAPI, flow_id: str, step_id: str, data: Dict[str, Any]
) -> Dict[str, Any]:
    """Complete a config flow step."""
    url = f"{api.url}/api/config/config_entries/flow/{flow_id}"
    # Home Assistant config flow API expects data directly in the payload, not nested
    payload = data.copy()

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=api.headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                try:
                    error_json = await response.json()
                    error_msg = error_json.get("message", error_text)
                    # Try to get more details
                    if "errors" in error_json:
                        error_msg += f"\nErrors: {error_json['errors']}"
                except:
                    error_msg = error_text
                raise Exception(
                    f"Config flow step failed (status {response.status}): {error_msg}\n"
                    f"URL: {url}\n"
                    f"Step ID: {step_id}\n"
                    f"Payload: {payload}"
                )
            return await response.json()


async def get_current_step_id(api: HomeAssistantAPI, flow_id: str) -> str:
    """Get the current step_id from the flow state."""
    flow_state = await get_flow_state(api, flow_id)
    return flow_state.get("step_id", "unknown")


async def select_menu_option(api: HomeAssistantAPI, flow_id: str, option: str) -> Dict[str, Any]:
    """Select an option from a menu step and return the flow result."""
    return await complete_flow_step(api, flow_id, "menu", {"next_step_id": option})


async def find_virtual_ac_sensors(
    api: HomeAssistantAPI,
    virtual_ac_entity_id: str,
) -> Dict[str, Optional[str]]:
    """
    Check if Virtual AC creates sensor entities for temperature and humidity.
    Returns dict with 'temp_sensor' (internal), 'external_temp_sensor', and 'humidity_sensor'
    entity IDs if found, None otherwise.
    """
    # Extract base name from Virtual AC entity ID
    base_name = virtual_ac_entity_id.replace("climate.", "")

    # Common patterns Virtual AC might use for sensor entities
    # Check most specific patterns first (indoor_temperature/humidity are the actual ones)
    possible_temp_sensors = [
        f"sensor.{base_name}_indoor_temperature",  # Actual Virtual AC sensor pattern
        f"sensor.{base_name}_temperature",
        f"sensor.{base_name}_temp",
        f"sensor.{base_name}_current_temperature",
    ]
    possible_external_temp_sensors = [
        f"sensor.{base_name}_ambient_temperature",  # External/ambient temperature
        f"sensor.{base_name}_outdoor_temperature",
        f"sensor.{base_name}_external_temperature",
    ]
    possible_humidity_sensors = [
        f"sensor.{base_name}_indoor_humidity",  # Actual Virtual AC sensor pattern
        f"sensor.{base_name}_humidity",
        f"sensor.{base_name}_current_humidity",
    ]

    temp_sensor = None
    external_temp_sensor = None
    humidity_sensor = None

    # Check for internal temperature sensor
    print(f"  🔍 Checking for internal temperature sensors: {possible_temp_sensors}")
    for sensor_id in possible_temp_sensors:
        try:
            state = await api.get_state(sensor_id)
            if state:
                temp_sensor = sensor_id
                print(f"  ✅ Found Virtual AC internal temperature sensor: {sensor_id}")
                break
        except Exception as e:
            # Silently continue - sensor doesn't exist
            continue

    if not temp_sensor:
        print(f"  ❌ No internal temperature sensor found")

    # Check for external/ambient temperature sensor
    print(f"  🔍 Checking for external temperature sensors: {possible_external_temp_sensors}")
    for sensor_id in possible_external_temp_sensors:
        try:
            state = await api.get_state(sensor_id)
            if state:
                external_temp_sensor = sensor_id
                print(f"  ✅ Found Virtual AC external temperature sensor: {sensor_id}")
                break
        except Exception as e:
            # Silently continue - sensor doesn't exist
            continue

    if not external_temp_sensor:
        print(f"  ❌ No external temperature sensor found (will use input_number)")

    # Check for humidity sensor
    print(f"  🔍 Checking for humidity sensors: {possible_humidity_sensors}")
    for sensor_id in possible_humidity_sensors:
        try:
            state = await api.get_state(sensor_id)
            if state:
                humidity_sensor = sensor_id
                print(f"  ✅ Found Virtual AC humidity sensor: {sensor_id}")
                break
        except Exception as e:
            # Silently continue - sensor doesn't exist
            continue

    if not humidity_sensor:
        print(f"  ❌ No humidity sensor found")

    return {
        "temp_sensor": temp_sensor,
        "external_temp_sensor": external_temp_sensor,
        "humidity_sensor": humidity_sensor,
    }


async def create_input_number(
    api: HomeAssistantAPI,
    entity_id: str,
    name: str,
    min_value: float = 0.0,
    max_value: float = 100.0,
    step: float = 0.1,
    unit: str = None,
    initial_value: float = None,
) -> bool:
    """
    Create an input_number or number entity via Home Assistant's config flow API.

    Note: input_number entities cannot be created via API - they must be in configuration.yaml.
    This function will try to create a 'number' helper instead, which Versatile Thermostat also accepts.
    Returns True if created successfully, False otherwise.
    """
    # input_number entities cannot be created via the REST API - they must be in configuration.yaml
    # This is a Home Assistant limitation, not a script limitation
    print(f"  ⚠️  Cannot create {entity_id} automatically.")
    print(f"  ⚠️  Home Assistant does not allow creating input_number entities via the REST API.")
    print(f"  ⚠️  They must be created manually in configuration.yaml or via the UI.")
    return False


async def ensure_input_number_exists(
    api: HomeAssistantAPI,
    entity_id: str,
    name: str,
    min_value: float = 0.0,
    max_value: float = 100.0,
    step: float = 0.1,
    unit: str = None,
    initial_value: float = None,
) -> bool:
    """
    Ensure an input_number entity exists. If it doesn't exist, try to create it.
    Returns True if entity exists (or was created), False otherwise.
    """
    try:
        # Try to get the entity state
        state = await api.get_state(entity_id)
        if state:
            # Entity exists - set initial value if provided
            if initial_value is not None:
                try:
                    await api.call_service(
                        "input_number",
                        "set_value",
                        {"entity_id": entity_id, "value": initial_value},
                    )
                    print(f"  ✅ Set initial value for {entity_id}: {initial_value}")
                except Exception as e:
                    print(f"  ⚠️  Could not set initial value for {entity_id}: {e}")
            return True
    except Exception as e:
        # Check if it's a 404 (entity doesn't exist) or other error
        error_str = str(e).lower()
        if "404" in error_str or "not found" in error_str:
            # Entity doesn't exist - try to create it
            print(f"  📝 Creating input_number entity: {entity_id}")
            created = await create_input_number(
                api, entity_id, name, min_value, max_value, step, unit, initial_value
            )
            if created:
                return True
            # If creation failed, provide instructions
            print(f"  ⚠️  Could not create {entity_id} automatically.")
        else:
            # Other error - re-raise it
            print(f"  ⚠️  Error checking {entity_id}: {e}")
            raise

    # Entity doesn't exist and couldn't be created - provide instructions
    entity_name = entity_id.split(".", 1)[-1] if "." in entity_id else entity_id
    unit_str = f"\n    unit_of_measurement: '{unit}'" if unit else ""
    print(f"\n  ❌ Entity {entity_id} does not exist and could not be created automatically.")
    print(f"  ⚠️  LIMITATION: input_number entities cannot be created via Home Assistant's REST API.")
    print(f"  ⚠️  They must be created manually in configuration.yaml or via the UI.")
    print(f"\n  📝 To fix this, add the following to your configuration.yaml:\n")
    print(f"input_number:\n")
    print(f"  {entity_name}:\n")
    print(f"    name: {name}\n")
    print(f"    min: {min_value}\n")
    print(f"    max: {max_value}\n")
    print(f"    step: {step}{unit_str}\n")
    if initial_value is not None:
        print(f"    initial: {initial_value}\n")
    print(f"  Then restart Home Assistant and run this script again.\n")
    print(f"  Alternatively, you can create it via the UI:")
    print(f"    Settings → Devices & Services → Helpers → Create Helper → Number\n")
    return False


def build_versatile_thermostat_config(
    name: str,
    temp_sensor_entity_id: str,
    virtual_ac_entity_id: str,
    humidity_sensor_entity_id: str = None,
    humidity_threshold: float = 60.0,
    cycle_min: int = 1,
    ac_mode: bool = True,
    enable_humidity: bool = True,
) -> Dict[str, Any]:
    """
    Build the complete config data structure for Versatile Thermostat.

    This function analyzes the config flow code to build the exact data structure
    that would be stored in the config entry after going through all the steps.

    Returns a dict with all the configuration data needed.
    """
    config = {
        # From user step
        "thermostat_type": "thermostat_over_climate",

        # From main step
        "name": name,
        "temperature_sensor_entity_id": temp_sensor_entity_id,
        "cycle_min": cycle_min,
        "device_power": 1.0,
        "use_main_central_config": False,
        "use_central_mode": False,

        # From spec_main step (when use_main_central_config=False)
        "external_temp_sensor": temp_sensor_entity_id,  # Use same sensor
        "temp_min": 16.0,
        "temp_max": 30.0,
        "step_temperature": 0.5,

        # From type step
        "underlying_entity_ids": [virtual_ac_entity_id],
        "ac_mode": ac_mode,
        "auto_regulation_mode": "auto_regulation_none",
        "auto_regulation_dtemp": 0.5,
        "auto_regulation_periode_min": 5,  # Note: "periode" not "period"
        "auto_fan_mode": "auto_fan_high",
        "auto_regulation_use_device_temp": False,

        # From features step
        "use_window_feature": False,
        "use_motion_feature": False,
        "use_power_feature": False,
        "use_presence_feature": False,
        "use_humidity_feature": enable_humidity,
        "use_auto_start_stop_feature": False,

        # From advanced step (defaults)
        "use_advanced_central_config": False,
        "safety_delay_min": 60,
        "safety_min_on_percent": 30.0,
        "safety_default_on_percent": 30.0,

        # From presets step (defaults)
        "use_presets_central_config": False,

        # From lock step (defaults)
        "use_lock_central_config": False,
    }

    # From humidity step (if enabled)
    if enable_humidity and humidity_sensor_entity_id:
        config["humidity_sensor_entity_id"] = humidity_sensor_entity_id
        config["use_humidity_central_config"] = False
        # From spec_humidity step (when use_humidity_central_config=False)
        config["humidity_threshold"] = humidity_threshold

    return config


def get_versatile_thermostat_instructions(
    name: str,
    virtual_ac_entity_id: str,
    temp_sensor_entity_id: str,
    external_temp_sensor_entity_id: str,
    humidity_sensor_entity_id: str = None,
    humidity_threshold: float = 60.0,
    cycle_min: int = 1,
    ac_mode: bool = True,
    enable_humidity: bool = True,
) -> str:
    """Generate instructions for creating a Versatile Thermostat."""
    instructions = f"""
To create the Versatile Thermostat '{name}':

1. Open Home Assistant UI
2. Go to Settings → Devices & Services → Add Integration
3. Search for "Versatile Thermostat" and select it
4. Follow the configuration wizard with these settings:

   STEP 1 - Select Type:
   - Choose: "Thermostat over Climate"

   STEP 2 - Main Configuration:
   - Name: {name}
   - Temperature Sensor (Internal): {temp_sensor_entity_id}
   - Cycle Min: {cycle_min}
   - Device Power: 1
   - Use Main Central Config: NO (unchecked)
   - Use Central Mode: NO (unchecked)

   STEP 3 - Specific Main Configuration:
   - External Temp Sensor: {external_temp_sensor_entity_id}
   - Min Temperature: 16.0°C
   - Max Temperature: 30.0°C
   - Step Temperature: 0.5°C

   STEP 4 - Type Configuration:
   - Underlying Climate Entity: {virtual_ac_entity_id}
   - AC Mode: {'YES' if ac_mode else 'NO'}
   - Auto Regulation Mode: None
   - Auto Regulation dTemp: 0.5°C
   - Auto Regulation Period: 5 minutes
   - Auto Fan Mode: High
   - Use Device Temperature: NO (unchecked)

   STEP 5 - Features:
   - Window Feature: NO
   - Motion Feature: NO
   - Power Feature: NO
   - Presence Feature: NO
   - Humidity Feature: {'YES' if enable_humidity else 'NO'}
   - Auto Start/Stop Feature: NO"""

    if enable_humidity and humidity_sensor_entity_id:
        instructions += f"""

   STEP 6 - Humidity Configuration:
   - Humidity Sensor: {humidity_sensor_entity_id}
   - Use Humidity Central Config: NO (unchecked)
   - Humidity Threshold: {humidity_threshold}%"""

    instructions += f"""

5. Complete the configuration
6. Verify the entity is created: climate.{name}

Expected entity ID: climate.{name}
"""
    return instructions


def get_sensor_instructions(entity_id: str, sensor_type: str = "temperature") -> str:
    """Generate instructions for creating a sensor entity."""
    entity_name = entity_id.split(".", 1)[-1] if "." in entity_id else entity_id

    if entity_id.startswith("input_number."):
        if sensor_type == "temperature":
            # Determine if this is external or internal based on entity name
            is_external = "external" in entity_name.lower() or "ambient" in entity_name.lower() or "outdoor" in entity_name.lower()
            sensor_label = "External Temperature" if is_external else "Internal Temperature"
            initial_value = 25.0 if is_external else 22.0  # External typically warmer

            instructions = f"""
To create the {sensor_label.lower()} sensor '{entity_id}':

OPTION 1 - Via configuration.yaml (recommended):
1. Open your configuration.yaml file
2. Add the following under 'input_number:':

  {entity_name}:
    name: {sensor_label}
    min: 0.0
    max: 50.0
    step: 0.1
    unit_of_measurement: "°C"
    initial: {initial_value}

3. Restart Home Assistant

OPTION 2 - Via UI:
1. Go to Settings → Devices & Services → Helpers
2. Click "Create Helper" → "Number"
3. Configure:
   - Name: {sensor_label}
   - Min: 0.0
   - Max: 50.0
   - Step: 0.1
   - Unit: °C
   - Initial: {initial_value}
4. Save

Expected entity ID: {entity_id}
"""
        else:  # humidity
            instructions = f"""
To create the humidity sensor '{entity_id}':

OPTION 1 - Via configuration.yaml (recommended):
1. Open your configuration.yaml file
2. Add the following under 'input_number:':

  {entity_name}:
    name: Test Humidity
    min: 0.0
    max: 100.0
    step: 0.1
    unit_of_measurement: "%"
    initial: 50.0

3. Restart Home Assistant

OPTION 2 - Via UI:
1. Go to Settings → Devices & Services → Helpers
2. Click "Create Helper" → "Number"
3. Configure:
   - Name: Test Humidity
   - Min: 0.0
   - Max: 100.0
   - Step: 0.1
   - Unit: %
   - Initial: 50.0
4. Save

Expected entity ID: {entity_id}
"""
    else:
        instructions = f"""
The sensor '{entity_id}' should be created automatically by Virtual AC.
If it doesn't exist, check that Virtual AC is properly configured and running.

Expected entity ID: {entity_id}
"""

    return instructions


async def check_versatile_thermostat_exists(
    api: HomeAssistantAPI,
    name: str,
    virtual_ac_entity_id: str,
    temp_sensor_entity_id: str,
    external_temp_sensor_entity_id: str,
    humidity_sensor_entity_id: str = None,
    humidity_threshold: float = 60.0,
    cycle_min: int = 1,
    ac_mode: bool = True,
    enable_humidity: bool = True,
) -> Dict[str, Any]:
    """Check if Versatile Thermostat exists, prompt for creation if not."""
    entity_id = f"climate.{name}"
    instructions = get_versatile_thermostat_instructions(
        name, virtual_ac_entity_id, temp_sensor_entity_id, external_temp_sensor_entity_id,
        humidity_sensor_entity_id, humidity_threshold,
        cycle_min, ac_mode, enable_humidity
    )

    state = await check_entity_exists(api, entity_id, "Versatile Thermostat", instructions)

    # Verify entity details
    print(f"\n✅ Versatile Thermostat entity verified:")
    print(f"   Entity ID: {entity_id}")
    print(f"   State: {state.get('state')}")
    attrs = state.get("attributes", {})
    print(f"   Current Temperature: {attrs.get('current_temperature')}°C")
    print(f"   Target Temperature: {attrs.get('temperature')}°C")
    if enable_humidity:
        print(f"   Current Humidity: {attrs.get('current_humidity')}%")
        print(f"   Humidity Configured: {attrs.get('humidity') is not None}")
    print(f"   HVAC Modes: {attrs.get('hvac_modes', [])}")

    return {
        "entity_id": entity_id,
        "state": state,
    }


async def setup_versatile_thermostat(
    api: HomeAssistantAPI,
    virtual_ac_entity_id: str,
    name: str,
    temp_sensor_entity_id: str = None,
    humidity_sensor_entity_id: str = None,
    humidity_threshold: float = 60.0,
    cycle_min: int = 1,
    ac_mode: bool = True,
    enable_humidity: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Check if Versatile Thermostat exists, prompt for creation if not.
    Also checks for required sensors and prompts for their creation if needed.

    Note: cycle_min defaults to 1 minute (instead of typical 5 minutes) because
    Virtual AC is a virtual device with no physical constraints, so faster cycles
    make tests run quicker without any risk.
    """
    print(f"\n🌡️  Setting up Versatile Thermostat: {name}")

    # Extract base name from Virtual AC entity ID
    if virtual_ac_entity_id.startswith("climate."):
        virtual_ac_base_name = virtual_ac_entity_id.replace("climate.", "")
    else:
        virtual_ac_base_name = name.lower().replace(" ", "_")

    # First, check if Virtual AC creates sensor entities we can use directly
    print("  📝 Checking if Virtual AC creates sensor entities...")
    print(f"  🔍 Looking for sensors for Virtual AC: {virtual_ac_entity_id}")
    virtual_ac_sensors = await find_virtual_ac_sensors(api, virtual_ac_entity_id)

    # Determine sensor entity IDs - prefer Virtual AC's sensor entities if they exist
    # Internal temperature sensor (for Versatile Thermostat control)
    if temp_sensor_entity_id:
        final_temp_sensor_id = temp_sensor_entity_id
        print(f"  ℹ️  Using provided internal temperature sensor: {final_temp_sensor_id}")
    elif virtual_ac_sensors["temp_sensor"]:
        final_temp_sensor_id = virtual_ac_sensors["temp_sensor"]
        print(f"  ✅ Using Virtual AC internal temperature sensor: {final_temp_sensor_id}")
    else:
        final_temp_sensor_id = f"input_number.{virtual_ac_base_name}_temp"
        print(f"  ⚠️  Virtual AC doesn't create internal temperature sensor, will use: {final_temp_sensor_id}")

    # External temperature sensor (for Versatile Thermostat external temp calculations)
    if virtual_ac_sensors["external_temp_sensor"]:
        final_external_temp_sensor_id = virtual_ac_sensors["external_temp_sensor"]
        print(f"  ✅ Using Virtual AC external temperature sensor: {final_external_temp_sensor_id}")
    else:
        final_external_temp_sensor_id = f"input_number.{virtual_ac_base_name}_external_temp"
        print(f"  ⚠️  Virtual AC doesn't create external temperature sensor, will use: {final_external_temp_sensor_id}")

    if enable_humidity:
        if humidity_sensor_entity_id:
            final_humidity_sensor_id = humidity_sensor_entity_id
        elif virtual_ac_sensors["humidity_sensor"]:
            final_humidity_sensor_id = virtual_ac_sensors["humidity_sensor"]
            print(f"  ✅ Using Virtual AC humidity sensor: {final_humidity_sensor_id}")
        else:
            final_humidity_sensor_id = f"input_number.{virtual_ac_base_name}_humidity"
            print(f"  ℹ️  Virtual AC doesn't create humidity sensor, will use: {final_humidity_sensor_id}")
    else:
        final_humidity_sensor_id = None

    # Check for required sensors - prompt for creation if needed
    print("  📝 Verifying required sensors exist...")

    # Check internal temperature sensor
    try:
        await api.get_state(final_temp_sensor_id)
        print(f"  ✅ Internal temperature sensor verified: {final_temp_sensor_id}")
    except Exception:
        instructions = get_sensor_instructions(final_temp_sensor_id, "temperature")
        await check_entity_exists(api, final_temp_sensor_id, "Internal Temperature Sensor", instructions)

    # Check external temperature sensor
    try:
        await api.get_state(final_external_temp_sensor_id)
        print(f"  ✅ External temperature sensor verified: {final_external_temp_sensor_id}")
    except Exception:
        instructions = get_sensor_instructions(final_external_temp_sensor_id, "temperature")
        await check_entity_exists(api, final_external_temp_sensor_id, "External Temperature Sensor", instructions)

    # Check humidity sensor if enabled
    if enable_humidity and final_humidity_sensor_id:
        try:
            await api.get_state(final_humidity_sensor_id)
            print(f"  ✅ Humidity sensor verified: {final_humidity_sensor_id}")
        except Exception:
            instructions = get_sensor_instructions(final_humidity_sensor_id, "humidity")
            await check_entity_exists(api, final_humidity_sensor_id, "Humidity Sensor", instructions)

    print("  ✅ All required sensors exist")

    # Check for Versatile Thermostat - prompt for creation if needed
    return await check_versatile_thermostat_exists(
        api,
        name,
        virtual_ac_entity_id,
        final_temp_sensor_id,
        final_external_temp_sensor_id,
        final_humidity_sensor_id,
        humidity_threshold,
        cycle_min,
        ac_mode,
        enable_humidity,
    )


async def setup_versatile_thermostat_old(
    api: HomeAssistantAPI,
    virtual_ac_entity_id: str,
    name: str,
    temp_sensor_entity_id: str = None,
    humidity_sensor_entity_id: str = None,
    humidity_threshold: float = 60.0,
    cycle_min: int = 1,
    ac_mode: bool = True,
    enable_humidity: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    OLD VERSION - Kept for reference. This function attempted to create Versatile Thermostat
    programmatically via the config flow API, which was complex and error-prone.
    """
    # This function is deprecated - use check_versatile_thermostat_exists instead
    raise NotImplementedError("This function is deprecated. Use check_versatile_thermostat_exists instead.")

    try:
        # Step 1: Start the flow (user step - select thermostat type)
        print("  📝 Step 1: Starting config flow...")
        flow_result = await create_versatile_thermostat_flow(api, name)
        flow_id = flow_result["flow_id"]
        print(f"  ✅ Flow started: {flow_id}")

        # Get the current flow state to see what step we're on
        flow_state = await get_flow_state(api, flow_id)
        current_step_id = flow_state.get("step_id", "user")
        print(f"  Current step_id: {current_step_id}")

        # Step 2: Select thermostat type (thermostat_over_climate)
        print("  📝 Step 2: Selecting thermostat type (thermostat_over_climate)...")
        try:
            flow_result = await complete_flow_step(
                api, flow_id, current_step_id, {"thermostat_type": "thermostat_over_climate"}
            )
            # Update flow_id if returned in response
            if "flow_id" in flow_result:
                flow_id = flow_result["flow_id"]
            print(f"  ✅ Thermostat type selected. Flow result type: {flow_result.get('type', 'unknown')}")
        except Exception as e:
            print(f"  ❌ Error completing step: {e}")
            # Get current flow state for debugging
            try:
                flow_state = await get_flow_state(api, flow_id)
                print(f"  Current flow state: {flow_state}")
            except:
                pass
            raise

        # Step 2.5: Select "main" from menu (if flow returned a menu)
        if flow_result.get("type") == "menu":
            print("  📝 Step 2.5: Selecting 'main' from menu...")
            flow_result = await select_menu_option(api, flow_id, "main")
            if "flow_id" in flow_result:
                flow_id = flow_result["flow_id"]
            print(f"  ✅ Menu selection complete. Flow result type: {flow_result.get('type', 'unknown')}, step_id: {flow_result.get('step_id')}")

        # Step 3: Main configuration
        print("  📝 Step 3: Configuring main settings...")
        # Use values from complete_config to ensure correct field names
        # Use local config (no central config) to have full control over all behaviors
        # Extract only the fields needed for the main step from complete_config
        main_data = {
            "name": complete_config["name"],
            "temperature_sensor_entity_id": complete_config["temperature_sensor_entity_id"],
            "cycle_min": complete_config["cycle_min"],
            "device_power": str(complete_config["device_power"]),  # API expects string
            "use_main_central_config": complete_config["use_main_central_config"],
            "use_central_mode": complete_config["use_central_mode"],
            # Note: used_by_controls_central_boiler is not allowed for over_climate thermostats
        }
        flow_result = await complete_flow_step(api, flow_id, "main", main_data)
        if "flow_id" in flow_result:
            flow_id = flow_result["flow_id"]
        result_type = flow_result.get("type", "unknown")
        result_step_id = flow_result.get("step_id", "unknown")
        result_errors = flow_result.get("errors", {})
        print(f"  ✅ Main settings configured. Flow result type: {result_type}, step_id: {result_step_id}")

        # Check for validation errors - if there are errors, the flow won't transition
        if result_errors:
            print(f"  ❌ Flow has validation errors: {result_errors}")
            # Check if it's an unknown entity error
            if "temperature_sensor_entity_id" in result_errors:
                error_msg = result_errors["temperature_sensor_entity_id"]
                if "unknown_entity" in str(error_msg):
                    raise Exception(
                        f"Temperature sensor {temp_sensor_entity_id} does not exist or is not accessible. "
                        f"Please ensure the sensor exists and Home Assistant can access it, then try again."
                    )
            # Other validation errors
            raise Exception(f"Config flow validation failed: {result_errors}. Please fix the errors and try again.")

        # Debug: print full flow result to understand what's happening (only if no errors)
        print(f"  🔍 Flow result: type={result_type}, step_id={result_step_id}")

        # Check if flow went to menu (shouldn't happen with use_main_central_config=False)
        if result_type == "menu":
            print("  ⚠️  Flow went to menu instead of spec_main - this shouldn't happen with use_main_central_config=False")
            # Continue to type step selection
            current_step_id = "menu"
            flow_state = {"type": "menu", "step_id": "menu"}
        elif result_type == "form" and result_step_id == "main":
            # Flow should have transitioned to spec_main (same step_id but different schema)
            # The transition happens internally - wait for it and check flow state
            print("  ⏳ Waiting for flow to transition to spec_main...")
            for attempt in range(3):
                await asyncio.sleep(0.5)
                flow_state = await get_flow_state(api, flow_id)
                current_step_id = flow_state.get("step_id", "unknown")
                flow_type = flow_state.get("type", "unknown")
                errors = flow_state.get("errors", {})
                print(f"  Attempt {attempt + 1}: Flow state - type={flow_type}, step_id={current_step_id}")
                if errors:
                    print(f"  ⚠️  Flow has errors: {errors}")

                # Try to complete spec_main
                if current_step_id == "main" and flow_type == "form":
                    print("  📝 Attempting to complete spec_main step...")
                    spec_main_data = {
                        "external_temp_sensor": complete_config["external_temp_sensor"],
                        "temp_min": complete_config["temp_min"],
                        "temp_max": complete_config["temp_max"],
                        "step_temperature": complete_config["step_temperature"],
                    }
                    try:
                        flow_result = await complete_flow_step(api, flow_id, "main", spec_main_data)
                        if "flow_id" in flow_result:
                            flow_id = flow_result["flow_id"]
                        await asyncio.sleep(0.5)
                        flow_state = await get_flow_state(api, flow_id)
                        current_step_id = flow_state.get("step_id", "unknown")
                        print(f"  ✅ spec_main completed successfully. Now on step: {current_step_id}")
                        break
                    except Exception as e:
                        error_str = str(e)
                        if "temperature_sensor_entity_id" in error_str or "name" in error_str:
                            print(f"  ⚠️  Attempt {attempt + 1} failed: Flow still expects main fields")
                            if attempt < 2:
                                print("  ⏳ Retrying after longer wait...")
                                await asyncio.sleep(1.0)
                                continue
                            else:
                                print(f"  ❌ Flow did not transition after 3 attempts. Last error: {e}")
                                flow_state = await get_flow_state(api, flow_id)
                                print(f"  Final flow state: {flow_state}")
                                raise Exception(f"Flow did not transition to spec_main. Flow state: {flow_state}")
                        else:
                            raise
                elif flow_type == "menu":
                    print("  ✅ Flow went to menu (spec_main may have been skipped)")
                    current_step_id = "menu"
                    break
                else:
                    current_step_id = flow_state.get("step_id", "unknown")
                    break
        else:
            # Unexpected result - check flow state
            await asyncio.sleep(0.5)
            flow_state = await get_flow_state(api, flow_id)
            current_step_id = flow_state.get("step_id", "unknown")
            print(f"  Flow state: type={flow_state.get('type')}, step_id={current_step_id}")

        # Navigate to type step via menu
        if current_step_id == "menu" or flow_state.get("type") == "menu":
            print("  📝 Selecting 'type' from menu...")
            flow_result = await select_menu_option(api, flow_id, "type")
            if "flow_id" in flow_result:
                flow_id = flow_result["flow_id"]
            await asyncio.sleep(0.5)
            flow_state = await get_flow_state(api, flow_id)
            current_step_id = flow_state.get("step_id", "unknown")
            print(f"  ✅ Menu selection complete. Now on step: {current_step_id}")

        # Step 4: Type configuration (underlying climate entity)
        print("  📝 Step 4: Configuring underlying climate entity...")
        if current_step_id != "type":
            raise Exception(f"Expected to be on 'type' step, but currently on '{current_step_id}'. Flow state: {flow_state}")
        print(f"  Confirmed on 'type' step: {current_step_id}")

        # Use values from complete_config to ensure correct field names and values
        type_data = {
            "underlying_entity_ids": complete_config["underlying_entity_ids"],  # Already a list
            "ac_mode": complete_config["ac_mode"],
            "auto_regulation_mode": complete_config["auto_regulation_mode"],
            "auto_regulation_dtemp": complete_config["auto_regulation_dtemp"],
            "auto_regulation_periode_min": complete_config["auto_regulation_periode_min"],
            "auto_fan_mode": complete_config["auto_fan_mode"],
            "auto_regulation_use_device_temp": complete_config["auto_regulation_use_device_temp"],
        }
        flow_result = await complete_flow_step(api, flow_id, current_step_id, type_data)
        if "flow_id" in flow_result:
            flow_id = flow_result["flow_id"]
        print("  ✅ Underlying entity configured")

        # If flow returned to menu, select "features" next
        if flow_result.get("type") == "menu":
            print("  📝 Selecting 'features' from menu...")
            flow_result = await select_menu_option(api, flow_id, "features")
            if "flow_id" in flow_result:
                flow_id = flow_result["flow_id"]

        # Step 5: Features configuration
        print("  📝 Step 5: Configuring features...")
        features_data = {
            "use_window_feature": False,
            "use_motion_feature": False,
            "use_power_feature": False,
            "use_presence_feature": False,
            "use_humidity_feature": enable_humidity,
            "use_auto_start_stop_feature": False,
        }
        flow_result = await complete_flow_step(api, flow_id, "features", features_data)
        if "flow_id" in flow_result:
            flow_id = flow_result["flow_id"]
        print("  ✅ Features configured")

        # If flow returned to menu and humidity is enabled, select "humidity" next
        if enable_humidity and flow_result.get("type") == "menu":
            print("  📝 Selecting 'humidity' from menu...")
            flow_result = await select_menu_option(api, flow_id, "humidity")
            if "flow_id" in flow_result:
                flow_id = flow_result["flow_id"]

        # Step 6: Humidity configuration (if enabled)
        if enable_humidity:
            print("  📝 Step 6: Configuring humidity control...")
            # Use the sensor ID we determined at the start
            if not final_humidity_sensor_id:
                raise Exception("Humidity sensor entity ID is required when humidity is enabled")
            humidity_sensor_entity_id = final_humidity_sensor_id

            # Step 6a: Humidity sensor configuration
            # When use_humidity_central_config is False, it goes to spec_humidity step
            humidity_data = {
                "humidity_sensor_entity_id": humidity_sensor_entity_id,  # Correct field name from CONF_HUMIDITY_SENSOR
                "use_humidity_central_config": False,  # Use local config
            }
            flow_result = await complete_flow_step(api, flow_id, "humidity", humidity_data)
            if "flow_id" in flow_result:
                flow_id = flow_result["flow_id"]
            print("  ✅ Humidity sensor configured")

            # Step 6b: When use_humidity_central_config is False, flow goes to spec_humidity
            # which uses STEP_CENTRAL_HUMIDITY_DATA_SCHEMA (threshold only)
            # The step_id stays as "humidity" but it's a different form
            current_step_id = await get_current_step_id(api, flow_id)
            if current_step_id == "humidity":  # spec_humidity step (keeps step_id as "humidity")
                print("  📝 Configuring humidity threshold (spec_humidity step)...")
                humidity_threshold_data = {
                    "humidity_threshold": humidity_threshold,
                }
                flow_result = await complete_flow_step(api, flow_id, "humidity", humidity_threshold_data)
                if "flow_id" in flow_result:
                    flow_id = flow_result["flow_id"]
                print("  ✅ Humidity threshold configured")
            elif current_step_id == "menu":
                print("  ✅ Humidity control configured (using central config)")
            else:
                raise Exception(f"Unexpected step after humidity config: {current_step_id}. Expected 'humidity' or 'menu'.")

        # If flow returned to menu, select "finalize" next
        if flow_result.get("type") == "menu":
            print("  📝 Selecting 'finalize' from menu...")
            flow_result = await select_menu_option(api, flow_id, "finalize")
            if "flow_id" in flow_result:
                flow_id = flow_result["flow_id"]

        # Step 7: Finalize
        print("  📝 Step 7: Finalizing configuration...")
        flow_result = await complete_flow_step(api, flow_id, "finalize", {})
        entry_id = flow_result.get("entry_id")
        print(f"  ✅ Configuration finalized: {entry_id}")

        # Wait for entity to be available and verify it exists
        entity_id = f"climate.{name.lower().replace(' ', '_')}"
        print(f"  ⏳ Waiting for entity: {entity_id}")

        # Retry checking for entity (up to 10 seconds)
        max_retries = 10
        retry_count = 0
        state = None

        while retry_count < max_retries:
            try:
                state = await api.get_state(entity_id)
                break
            except Exception:
                retry_count += 1
                await asyncio.sleep(1)

        if state:
            attrs = state.get("attributes", {})
            print(f"  ✅ Versatile Thermostat entity verified:")
            print(f"     Entity ID: {entity_id}")
            print(f"     State: {state.get('state')}")
            print(f"     Current Temperature: {attrs.get('current_temperature')}°C")
            print(f"     Target Temperature: {attrs.get('temperature')}°C")
            if enable_humidity:
                print(f"     Current Humidity: {attrs.get('current_humidity')}%")
                print(f"     Humidity Configured: {attrs.get('is_humidity_configured', False)}")
            print(f"     HVAC Modes: {attrs.get('hvac_modes')}")

            # Sync Virtual AC state to input_number sensors
            print("  🔄 Syncing Virtual AC state to sensors...")
            await sync_virtual_ac_to_sensors(
                api,
                virtual_ac_entity_id,
                temp_sensor_entity_id,
                humidity_sensor_entity_id if enable_humidity else None,
                verbose=True,
            )

            return {
                "entry_id": entry_id,
                "entity_id": entity_id,
                "name": name,
                "temp_sensor": temp_sensor_entity_id,
                "humidity_sensor": humidity_sensor_entity_id if enable_humidity else None,
            }
        else:
            raise Exception(f"Versatile Thermostat entity {entity_id} not found after {max_retries} seconds. Entry ID: {entry_id}")

    except Exception as e:
        print(f"  ❌ Failed to create Versatile Thermostat: {e}")
        import traceback

        traceback.print_exc()
        raise


async def test_simple_cooling(api: HomeAssistantAPI, entity_id: str) -> bool:
    """Test 1: Simple cooling in instant mode."""
    print("\n🧪 Test 1: Simple Cooling (Instant Mode)")
    print("=" * 50)

    # Set initial conditions
    await api.call_service(
        "virtual_ac",
        "set_state",
        {
            "entity_id": entity_id,
            "current_temperature": 25.0,
            "current_humidity": 50.0,
        },
    )
    print("✅ Set initial temp: 25°C")

    # Set target temperature
    await api.call_service(
        "climate", "set_temperature", {"entity_id": entity_id, "temperature": 22.0}
    )
    print("✅ Set target temp: 22°C")

    # Set to cool mode
    await api.call_service(
        "climate", "set_hvac_mode", {"entity_id": entity_id, "hvac_mode": "cool"}
    )
    print("✅ Set mode: COOL")

    # Wait a moment for instant mode
    await asyncio.sleep(2)

    # Check result
    state = await api.get_state(entity_id)
    current_temp = state.get("attributes", {}).get("current_temperature")
    hvac_mode = state.get("state")

    print(f"📊 Current temp: {current_temp}°C")
    print(f"📊 HVAC mode: {hvac_mode}")

    success = current_temp == 22.0 and hvac_mode == "cool"
    print(f"{'✅ PASS' if success else '❌ FAIL'}")
    return success


async def test_temperature_ramp(api: HomeAssistantAPI, entity_id: str) -> bool:
    """Test 2: Temperature ramp in realistic mode."""
    print("\n🧪 Test 2: Temperature Ramp (Realistic Mode)")
    print("=" * 50)

    # Set initial conditions
    await api.call_service(
        "virtual_ac",
        "set_state",
        {
            "entity_id": entity_id,
            "current_temperature": 25.0,
            "current_humidity": 50.0,
        },
    )
    print("✅ Set initial temp: 25°C")

    # Set target temperature
    await api.call_service(
        "climate", "set_temperature", {"entity_id": entity_id, "temperature": 20.0}
    )
    print("✅ Set target temp: 20°C")

    # Set to cool mode
    await api.call_service(
        "climate", "set_hvac_mode", {"entity_id": entity_id, "hvac_mode": "cool"}
    )
    print("✅ Set mode: COOL")

    # Monitor temperature change
    print("⏳ Monitoring temperature change...")
    start_temp = 25.0
    target_temp = 20.0
    check_count = 0
    max_checks = 30  # 30 seconds with 1s intervals

    while check_count < max_checks:
        state = await api.get_state(entity_id)
        current_temp = state.get("attributes", {}).get("current_temperature")
        print(f"   Temp: {current_temp:.2f}°C (target: {target_temp}°C)")

        if current_temp <= target_temp + 0.5:  # Within 0.5°C of target
            print(f"✅ Temperature reached target: {current_temp:.2f}°C")
            return True

        await asyncio.sleep(1)
        check_count += 1

    print("❌ Temperature did not reach target in time")
    return False


async def test_humidity_control_with_versatile_thermostat(
    api: HomeAssistantAPI,
    virtual_ac_entity_id: str,
    vtherm_entity_id: str,
    temp_sensor_entity_id: str,
    humidity_sensor_entity_id: str,
) -> bool:
    """Test humidity control: DRY mode activation when humidity is high."""
    print("\n🧪 Test: Humidity Control with Versatile Thermostat")
    print("=" * 50)

    try:
        # Step 1: Set initial conditions - temp at target, humidity below threshold
        print("📝 Step 1: Setting initial conditions...")
        await api.call_service(
            "virtual_ac",
            "set_state",
            {
                "entity_id": virtual_ac_entity_id,
                "current_temperature": 22.0,
                "current_humidity": 55.0,  # Below threshold (60%)
            },
        )
        # Sync Virtual AC state to sensors
        await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
        await asyncio.sleep(2)
        print("  ✅ Initial conditions set: temp=22°C, humidity=55%")

        # Step 2: Set Versatile Thermostat to COOL mode with target temp = current temp
        print("📝 Step 2: Configuring Versatile Thermostat...")
        await api.call_service(
            "climate",
            "set_temperature",
            {"entity_id": vtherm_entity_id, "temperature": 22.0},
        )
        await api.call_service(
            "climate",
            "set_hvac_mode",
            {"entity_id": vtherm_entity_id, "hvac_mode": "cool"},
        )
        await asyncio.sleep(3)
        print("  ✅ Versatile Thermostat set to COOL mode, target=22°C")

        # Step 3: Increase humidity above threshold
        print("📝 Step 3: Increasing humidity above threshold...")
        await api.call_service(
            "virtual_ac",
            "set_state",
            {
                "entity_id": virtual_ac_entity_id,
                "current_humidity": 65.0,  # Above threshold (60%)
            },
        )
        # Sync Virtual AC state to sensors
        await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
        await asyncio.sleep(2)
        print("  ✅ Humidity increased to 65%")

        # Step 4: Wait for Versatile Thermostat to switch to DRY mode
        print("📝 Step 4: Waiting for DRY mode activation...")
        max_checks = 30
        check_count = 0
        while check_count < max_checks:
            vtherm_state = await api.get_state(vtherm_entity_id)
            hvac_mode = vtherm_state.get("state")
            hvac_reason = vtherm_state.get("attributes", {}).get("specific_states", {}).get("hvac_reason")

            print(f"   Check {check_count + 1}/{max_checks}: mode={hvac_mode}, reason={hvac_reason}")

            if hvac_mode == "dry":
                print(f"  ✅ DRY mode activated! Reason: {hvac_reason}")
                return True

            await asyncio.sleep(2)
            check_count += 1

        print("  ❌ DRY mode did not activate within timeout")
        return False

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_cool_priority_over_dry(
    api: HomeAssistantAPI,
    virtual_ac_entity_id: str,
    vtherm_entity_id: str,
    temp_sensor_entity_id: str,
    humidity_sensor_entity_id: str,
) -> bool:
    """Test that COOL mode takes priority when cooling is needed.

    This test verifies that when both conditions are met:
    - High humidity (should trigger DRY mode)
    - Current temp significantly above target (should trigger COOL mode)

    COOL mode should take priority because temperature control is more critical.
    """
    print("\n🧪 Test: COOL Mode Priority Over DRY")
    print("=" * 50)

    try:
        # Step 1: Set conditions for DRY mode (high humidity, temp at target)
        print("📝 Step 1: Setting conditions for DRY mode...")
        await api.call_service(
            "virtual_ac",
            "set_state",
            {
                "entity_id": virtual_ac_entity_id,
                "current_temperature": 22.0,
                "current_humidity": 65.0,  # High humidity
            },
        )
        # Sync Virtual AC state to sensors
        await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
        await api.call_service(
            "climate",
            "set_temperature",
            {"entity_id": vtherm_entity_id, "temperature": 22.0},
        )
        await asyncio.sleep(3)
        print("  ✅ Conditions set: temp=22°C, humidity=65%, target=22°C")

        # Step 2: Wait for DRY mode (if it activates)
        print("📝 Step 2: Checking current mode...")
        await asyncio.sleep(5)
        vtherm_state = await api.get_state(vtherm_entity_id)
        initial_mode = vtherm_state.get("state")
        print(f"  Current mode: {initial_mode}")

        # Step 3: Lower target temperature significantly to require cooling
        # Use a larger difference (3°C) to ensure cooling is clearly needed
        print("📝 Step 3: Lowering target temperature to require cooling...")
        await api.call_service(
            "climate",
            "set_temperature",
            {"entity_id": vtherm_entity_id, "temperature": 19.0},  # 3°C below current (22°C)
        )
        # Ensure sensors are synced so Versatile Thermostat sees the temperature difference
        await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
        await asyncio.sleep(2)

        # Verify sensor values
        try:
            temp_sensor_state = await api.get_state(temp_sensor_entity_id)
            sensor_temp = temp_sensor_state.get("state")
            print(f"  📊 Temperature sensor value: {sensor_temp}°C")
        except Exception as e:
            print(f"  ⚠️  Could not read temperature sensor: {e}")

        # Verify the temperature difference
        vtherm_state = await api.get_state(vtherm_entity_id)
        current_temp = vtherm_state.get("attributes", {}).get("current_temperature")
        target_temp = vtherm_state.get("attributes", {}).get("temperature")
        print(f"  ✅ Target temperature set to {target_temp}°C (current: {current_temp}°C, diff: {current_temp - target_temp:.1f}°C)")
        if current_temp and target_temp and (current_temp - target_temp) < 2.0:
            print(f"  ⚠️  Warning: Temperature difference ({current_temp - target_temp:.1f}°C) may be too small to trigger COOL mode")

        # If current temp is not above target, we need to adjust
        if current_temp is None or current_temp <= target_temp:
            print(f"  ⚠️  Warning: Current temperature ({current_temp}°C) is not above target ({target_temp}°C)")
            print(f"  📝 Ensuring current temp is above target...")
            await api.call_service(
                "virtual_ac",
                "set_state",
                {
                    "entity_id": virtual_ac_entity_id,
                    "current_temperature": 22.0,  # Ensure it's above target
                },
            )
            await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
            await asyncio.sleep(2)
            vtherm_state = await api.get_state(vtherm_entity_id)
            current_temp = vtherm_state.get("attributes", {}).get("current_temperature")
            print(f"  ✅ Current temperature verified: {current_temp}°C")

        # Step 4: Wait for COOL mode activation
        print("📝 Step 4: Waiting for COOL mode...")
        max_checks = 30
        check_count = 0
        while check_count < max_checks:
            vtherm_state = await api.get_state(vtherm_entity_id)
            hvac_mode = vtherm_state.get("state")
            current_temp = vtherm_state.get("attributes", {}).get("current_temperature")
            target_temp = vtherm_state.get("attributes", {}).get("temperature")
            hvac_reason = vtherm_state.get("attributes", {}).get("specific_states", {}).get("hvac_reason", "N/A")

            print(f"   Check {check_count + 1}/{max_checks}: mode={hvac_mode}, temp={current_temp}°C, target={target_temp}°C, reason={hvac_reason}")

            if hvac_mode == "cool":
                print(f"  ✅ COOL mode activated (took priority over DRY)")
                return True

            await asyncio.sleep(2)
            check_count += 1

        print("  ❌ COOL mode did not activate within timeout")
        return False

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
    return False


async def test_dry_mode_deactivation(
    api: HomeAssistantAPI,
    virtual_ac_entity_id: str,
    vtherm_entity_id: str,
    temp_sensor_entity_id: str,
    humidity_sensor_entity_id: str,
) -> bool:
    """Test that DRY mode deactivates when humidity drops below threshold."""
    print("\n🧪 Test: DRY Mode Deactivation")
    print("=" * 50)

    try:
        # Step 1: Set up conditions for DRY mode (high humidity, temp at target)
        print("📝 Step 1: Setting conditions for DRY mode...")
        await api.call_service(
            "virtual_ac",
            "set_state",
            {
                "entity_id": virtual_ac_entity_id,
                "current_temperature": 22.0,
                "current_humidity": 65.0,  # Above threshold
            },
        )
        await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
        await api.call_service(
            "climate",
            "set_temperature",
            {"entity_id": vtherm_entity_id, "temperature": 22.0},
        )
        await api.call_service(
            "climate",
            "set_hvac_mode",
            {"entity_id": vtherm_entity_id, "hvac_mode": "cool"},
        )
        await asyncio.sleep(5)
        print("  ✅ Conditions set: temp=22°C, humidity=65%, target=22°C, mode=COOL")

        # Step 2: Wait for DRY mode to activate
        print("📝 Step 2: Waiting for DRY mode activation...")
        max_checks = 30
        check_count = 0
        dry_activated = False
        while check_count < max_checks:
            vtherm_state = await api.get_state(vtherm_entity_id)
            hvac_mode = vtherm_state.get("state")
            print(f"   Check {check_count + 1}/{max_checks}: mode={hvac_mode}")

            if hvac_mode == "dry":
                dry_activated = True
                print(f"  ✅ DRY mode activated")
                break

            await asyncio.sleep(2)
            check_count += 1

        if not dry_activated:
            print("  ⚠️  DRY mode did not activate, but continuing test...")

        # Step 3: Decrease humidity below threshold
        print("📝 Step 3: Decreasing humidity below threshold...")
        await api.call_service(
            "virtual_ac",
            "set_state",
            {
                "entity_id": virtual_ac_entity_id,
                "current_humidity": 55.0,  # Below threshold (60%)
            },
        )
        await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
        await asyncio.sleep(2)
        print("  ✅ Humidity decreased to 55%")

        # Step 4: Wait for COOL mode activation (DRY should deactivate)
        print("📝 Step 4: Waiting for COOL mode activation...")
        max_checks = 30
        check_count = 0
        while check_count < max_checks:
            vtherm_state = await api.get_state(vtherm_entity_id)
            hvac_mode = vtherm_state.get("state")
            is_too_high = vtherm_state.get("attributes", {}).get("humidity_manager", {}).get("is_humidity_too_high")

            print(f"   Check {check_count + 1}/{max_checks}: mode={hvac_mode}, humidity_too_high={is_too_high}")

            if hvac_mode == "cool":
                print(f"  ✅ COOL mode activated (DRY mode deactivated)")
                return True

            await asyncio.sleep(2)
            check_count += 1

        print("  ❌ COOL mode did not activate within timeout")
        return False

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_temperature_threshold_boundary(
    api: HomeAssistantAPI,
    virtual_ac_entity_id: str,
    vtherm_entity_id: str,
    temp_sensor_entity_id: str,
    humidity_sensor_entity_id: str,
) -> bool:
    """Test temperature threshold boundary conditions for DRY vs COOL mode selection."""
    print("\n🧪 Test: Temperature Threshold Boundary")
    print("=" * 50)

    try:
        base_temp = 22.0
        results = []

        # Set up initial conditions: high humidity, temp at target
        print("📝 Setting up initial conditions...")
        await api.call_service(
            "virtual_ac",
            "set_state",
            {
                "entity_id": virtual_ac_entity_id,
                "current_temperature": base_temp,
                "current_humidity": 65.0,  # High humidity
            },
        )
        await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
        await api.call_service(
            "climate",
            "set_hvac_mode",
            {"entity_id": vtherm_entity_id, "hvac_mode": "cool"},
        )
        await asyncio.sleep(3)
        print("  ✅ Initial conditions set: temp=22°C, humidity=65%")

        # Part A: Temperature at target (0.0°C difference) - Should use DRY
        print("\n📝 Part A: Temperature at target (0.0°C difference)...")
        await api.call_service(
            "climate",
            "set_temperature",
            {"entity_id": vtherm_entity_id, "temperature": base_temp},
        )
        await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
        await asyncio.sleep(5)

        vtherm_state = await api.get_state(vtherm_entity_id)
        hvac_mode = vtherm_state.get("state")
        current_temp = vtherm_state.get("attributes", {}).get("current_temperature")
        target_temp = vtherm_state.get("attributes", {}).get("temperature")
        print(f"  Current temp: {current_temp}°C, Target: {target_temp}°C, Mode: {hvac_mode}")
        part_a_passed = hvac_mode == "dry"
        results.append(part_a_passed)
        print(f"  {'✅ PASS' if part_a_passed else '❌ FAIL'}: Expected DRY mode, got {hvac_mode}")

        # Part B: Temperature just below threshold (0.05°C difference) - Should use DRY
        print("\n📝 Part B: Temperature within 0.1°C threshold (0.05°C difference)...")
        await api.call_service(
            "climate",
            "set_temperature",
            {"entity_id": vtherm_entity_id, "temperature": base_temp - 0.05},
        )
        await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
        await asyncio.sleep(5)

        vtherm_state = await api.get_state(vtherm_entity_id)
        hvac_mode = vtherm_state.get("state")
        current_temp = vtherm_state.get("attributes", {}).get("current_temperature")
        target_temp = vtherm_state.get("attributes", {}).get("temperature")
        print(f"  Current temp: {current_temp}°C, Target: {target_temp}°C, Mode: {hvac_mode}")
        part_b_passed = hvac_mode == "dry"
        results.append(part_b_passed)
        print(f"  {'✅ PASS' if part_b_passed else '❌ FAIL'}: Expected DRY mode, got {hvac_mode}")

        # Part C: Temperature above threshold (0.2°C difference) - Should use COOL
        print("\n📝 Part C: Temperature above 0.1°C threshold (0.2°C difference)...")
        await api.call_service(
            "climate",
            "set_temperature",
            {"entity_id": vtherm_entity_id, "temperature": base_temp - 0.2},
        )
        await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
        await asyncio.sleep(5)

        vtherm_state = await api.get_state(vtherm_entity_id)
        hvac_mode = vtherm_state.get("state")
        current_temp = vtherm_state.get("attributes", {}).get("current_temperature")
        target_temp = vtherm_state.get("attributes", {}).get("temperature")
        print(f"  Current temp: {current_temp}°C, Target: {target_temp}°C, Mode: {hvac_mode}")
        part_c_passed = hvac_mode == "cool"
        results.append(part_c_passed)
        print(f"  {'✅ PASS' if part_c_passed else '❌ FAIL'}: Expected COOL mode, got {hvac_mode}")

        all_passed = all(results)
        print(f"\n{'✅ ALL PARTS PASSED' if all_passed else '❌ SOME PARTS FAILED'}: {sum(results)}/3 parts")
        return all_passed

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_non_cool_mode_ignored(
    api: HomeAssistantAPI,
    virtual_ac_entity_id: str,
    vtherm_entity_id: str,
    temp_sensor_entity_id: str,
    humidity_sensor_entity_id: str,
) -> bool:
    """Test that humidity control does not interfere with non-COOL modes (e.g., HEAT)."""
    print("\n🧪 Test: Non-COOL Mode Ignored")
    print("=" * 50)

    try:
        # Step 1: Set to HEAT mode with high humidity
        print("📝 Step 1: Setting HEAT mode with high humidity...")
        await api.call_service(
            "virtual_ac",
            "set_state",
            {
                "entity_id": virtual_ac_entity_id,
                "current_temperature": 20.0,
                "current_humidity": 70.0,  # High humidity
            },
        )
        await sync_virtual_ac_to_sensors(api, virtual_ac_entity_id, temp_sensor_entity_id, humidity_sensor_entity_id)
        await api.call_service(
            "climate",
            "set_temperature",
            {"entity_id": vtherm_entity_id, "temperature": 22.0},
        )
        await api.call_service(
            "climate",
            "set_hvac_mode",
            {"entity_id": vtherm_entity_id, "hvac_mode": "heat"},
        )
        await asyncio.sleep(5)
        print("  ✅ Set HEAT mode with temp=20°C, target=22°C, humidity=70%")

        # Step 2: Verify HEAT mode is maintained (humidity control should not interfere)
        print("📝 Step 2: Verifying HEAT mode is maintained...")
        vtherm_state = await api.get_state(vtherm_entity_id)
        hvac_mode = vtherm_state.get("state")
        is_too_high = vtherm_state.get("attributes", {}).get("humidity_manager", {}).get("is_humidity_too_high")
        current_humidity = vtherm_state.get("attributes", {}).get("current_humidity")

        print(f"  HVAC Mode: {hvac_mode}")
        print(f"  Humidity Too High: {is_too_high}")
        print(f"  Current Humidity: {current_humidity}%")

        if hvac_mode == "heat":
            print(f"  ✅ HEAT mode maintained (humidity control does not interfere)")
            return True
        else:
            print(f"  ❌ Expected HEAT mode, got {hvac_mode}")
            return False

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_mode_switching(api: HomeAssistantAPI, entity_id: str) -> bool:
    """Test 3: Mode switching."""
    print("\n🧪 Test 3: Mode Switching")
    print("=" * 50)

    modes = ["cool", "heat", "dry", "fan_only", "off"]
    results = []

    for mode in modes:
        print(f"\n🔄 Switching to {mode.upper()} mode...")
        await api.call_service(
            "climate", "set_hvac_mode", {"entity_id": entity_id, "hvac_mode": mode}
        )
        await asyncio.sleep(1)

        state = await api.get_state(entity_id)
        current_mode = state.get("state")
        success = current_mode == mode
        results.append(success)
        print(f"   {'✅' if success else '❌'} Mode: {current_mode}")

    all_passed = all(results)
    print(f"\n{'✅ PASS' if all_passed else '❌ FAIL'}: {sum(results)}/{len(modes)} modes")
    return all_passed


async def cleanup_test_device(api: HomeAssistantAPI, entry_id: str) -> None:
    """Remove test device."""
    print(f"\n🧹 Cleaning up entry: {entry_id}")
    try:
        await api.delete_config_entry(entry_id)
        print("✅ Device removed")
    except Exception as e:
        print(f"⚠️  Failed to remove device: {e}")


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test Virtual AC with Versatile Thermostat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
    HASS_URL          Home Assistant URL (default: http://localhost:8123)
    HASS_TOKEN        Home Assistant API token (required if --token not provided)
    HASS_MODE         Test mode: instant (recommended), realistic, or fast-realistic (default: instant)
    HASS_TEST_TYPE    Test type: virtual-ac-only or integrated (default: integrated)
    HASS_CLEANUP       Set to 'true' to clean up after tests (default: false)
    HASS_TEMP_SENSOR   Temperature sensor entity_id
    HASS_HUMIDITY_SENSOR  Humidity sensor entity_id
    HASS_AC_NAME       Virtual AC device name (default: test_virtual_ac)
    HASS_VTHERM_NAME   Versatile Thermostat device name (default: test_versatile_thermostat)
        """,
    )
    parser.add_argument(
        "--url",
        default=os.getenv("HASS_URL", "http://localhost:8123"),
        help="Home Assistant URL (default: HASS_URL env var or http://localhost:8123)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("HASS_TOKEN"),
        help="Home Assistant API token (default: HASS_TOKEN env var)",
    )
    parser.add_argument(
        "--mode",
        choices=["instant", "realistic", "fast-realistic"],
        default=os.getenv("HASS_MODE", "instant"),
        help="Test mode: 'instant' (recommended for testing - fast, deterministic), "
             "'realistic' (gradual changes), or 'fast-realistic' (accelerated realistic). "
             "Default: HASS_MODE env var or 'instant'",
    )
    parser.add_argument(
        "--test-type",
        choices=["virtual-ac-only", "integrated"],
        default=os.getenv("HASS_TEST_TYPE", "integrated"),
        help="Test type: virtual-ac-only or integrated (default: HASS_TEST_TYPE env var or 'integrated')",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        default=os.getenv("HASS_CLEANUP", "").lower() in ("true", "1", "yes"),
        help="Clean up after tests (default: HASS_CLEANUP env var or false)",
    )
    parser.add_argument(
        "--temp-sensor",
        default=os.getenv("HASS_TEMP_SENSOR"),
        help="Temperature sensor entity_id (default: HASS_TEMP_SENSOR env var)",
    )
    parser.add_argument(
        "--humidity-sensor",
        default=os.getenv("HASS_HUMIDITY_SENSOR"),
        help="Humidity sensor entity_id (default: HASS_HUMIDITY_SENSOR env var)",
    )
    parser.add_argument(
        "--ac-name",
        default=os.getenv("HASS_AC_NAME", "test_virtual_ac"),
        help="Virtual AC device name (default: HASS_AC_NAME env var or 'test_virtual_ac')",
    )
    parser.add_argument(
        "--vtherm-name",
        default=os.getenv("HASS_VTHERM_NAME", "test_versatile_thermostat"),
        help="Versatile Thermostat device name (default: HASS_VTHERM_NAME env var or 'test_versatile_thermostat')",
    )
    args = parser.parse_args()

    # Validate required arguments
    if not args.token:
        parser.error("--token or HASS_TOKEN environment variable is required")

    api = HomeAssistantAPI(args.url, args.token)

    # Use consistent names for easier debugging
    ac_name = args.ac_name
    vtherm_name = args.vtherm_name
    print(f"\n🚀 Starting tests")
    print(f"   Virtual AC name: {ac_name}")
    print(f"   Versatile Thermostat name: {vtherm_name}")
    print(f"   Mode: {args.mode}")
    print(f"   Test type: {args.test_type}")

    virtual_ac = None
    versatile_thermostat = None
    try:
        # Create Virtual AC
        instant_mode = args.mode == "instant"
        fast_realistic = args.mode == "fast-realistic"
        virtual_ac = await create_virtual_ac(
            api, ac_name, instant_mode=instant_mode, fast_realistic=fast_realistic
        )
        virtual_ac_entity_id = virtual_ac["entity_id"]

        # Wait for Virtual AC to be ready
        print("\n⏳ Waiting for Virtual AC to be ready...")
        await asyncio.sleep(5)

        results = []

        if args.test_type == "virtual-ac-only":
            # Run Virtual AC only tests
            if instant_mode:
                results.append(await test_simple_cooling(api, virtual_ac_entity_id))
                results.append(await test_mode_switching(api, virtual_ac_entity_id))
            else:
                results.append(await test_temperature_ramp(api, virtual_ac_entity_id))
                results.append(await test_mode_switching(api, virtual_ac_entity_id))

        else:
            # Integrated tests with Versatile Thermostat
            print("\n" + "=" * 50)
            print("🔗 INTEGRATED TESTS")
            print("=" * 50)

            # Set up sensor entities (input_number - script handles syncing from Virtual AC)
            temp_sensor = args.temp_sensor or f"input_number.{vtherm_name}_temp"
            humidity_sensor = args.humidity_sensor or f"input_number.{vtherm_name}_humidity"

            print(f"\n📡 Sensor entities (input_number):")
            print(f"   Temperature: {temp_sensor}")
            print(f"   Humidity: {humidity_sensor}")
            print(f"   Note: Script automatically syncs Virtual AC state to these sensors")

            # Create Versatile Thermostat
            versatile_thermostat = await setup_versatile_thermostat(
                api,
                virtual_ac_entity_id,
                vtherm_name,
                temp_sensor_entity_id=temp_sensor,
                humidity_sensor_entity_id=humidity_sensor,
                humidity_threshold=60.0,
                cycle_min=1,
                ac_mode=True,
                enable_humidity=True,
            )

            if not versatile_thermostat:
                print("❌ Failed to create Versatile Thermostat. Skipping integrated tests.")
            else:
                vtherm_entity_id = versatile_thermostat["entity_id"]

                # Wait for Versatile Thermostat to be ready
                print("\n⏳ Waiting for Versatile Thermostat to be ready...")
                await asyncio.sleep(5)

                # Sync initial Virtual AC state to sensors
                print("\n🔄 Syncing Virtual AC state to sensors...")
                await sync_virtual_ac_to_sensors(
                    api, virtual_ac_entity_id, temp_sensor, humidity_sensor
                )

                # Run integrated tests
                results.append(
                    await test_humidity_control_with_versatile_thermostat(
                        api,
                        virtual_ac_entity_id,
                        vtherm_entity_id,
                        temp_sensor,
                        humidity_sensor,
                    )
                )
                results.append(
                    await test_cool_priority_over_dry(
                        api,
                        virtual_ac_entity_id,
                        vtherm_entity_id,
                        temp_sensor,
                        humidity_sensor,
                    )
                )
                results.append(
                    await test_dry_mode_deactivation(
                        api,
                        virtual_ac_entity_id,
                        vtherm_entity_id,
                        temp_sensor,
                        humidity_sensor,
                    )
                )
                results.append(
                    await test_temperature_threshold_boundary(
                        api,
                        virtual_ac_entity_id,
                        vtherm_entity_id,
                        temp_sensor,
                        humidity_sensor,
                    )
                )
                results.append(
                    await test_non_cool_mode_ignored(
                        api,
                        virtual_ac_entity_id,
                        vtherm_entity_id,
                        temp_sensor,
                        humidity_sensor,
                    )
                )

        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        passed = sum(results)
        total = len(results)
        print(f"Passed: {passed}/{total}")
        print(f"{'✅ ALL TESTS PASSED' if passed == total else '❌ SOME TESTS FAILED'}")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        if args.cleanup:
            if versatile_thermostat:
                print(f"\n🧹 Cleaning up Versatile Thermostat...")
                await cleanup_test_device(api, versatile_thermostat["entry_id"])
            if virtual_ac:
                print(f"\n🧹 Cleaning up Virtual AC...")
            await cleanup_test_device(api, virtual_ac["entry_id"])


if __name__ == "__main__":
    asyncio.run(main())
