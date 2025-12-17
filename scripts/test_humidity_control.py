#!/usr/bin/env python3
"""
Home Assistant Script for Automated Humidity Control Testing

This script automates the test scenarios for the Versatile Thermostat humidity control feature.
It steps through each test scenario, verifies expected results, and logs the results to a file.

Usage:
    python3 test_humidity_control.py

Prerequisites:
    - Home Assistant must be running
    - HASS_TOKEN environment variable set (or use --token)
    - HASS_URL environment variable set (or use --url, default: http://localhost:8123)
    - Test entities configured (thermostat, humidity sensor)
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from homeassistant_api import Client
    from homeassistant_api.errors import (
        UnauthorizedError,
        RequestError,
        MalformedDataError,
    )
except ImportError:
    print("ERROR: homeassistant_api not installed. Install with: pip install homeassistant-api")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Test configuration - UPDATE THESE FOR YOUR SETUP
DEFAULT_CONFIG = {
    "thermostat_entity": "climate.butlers_pantry_ac_versatile",  # Update to your thermostat entity
    "humidity_sensor": "input_number.test_humidity",  # Update to your humidity sensor
    "humidity_threshold": 60.0,  # Default threshold
    "wait_time": None,  # Will be calculated from cycle_min (default: 1.5 cycles)
    "cycle_multiplier": 1.5,  # Wait 1.5x cycle time to avoid short cycling
    "max_wait_time": None,  # Will be calculated from cycle_min (default: 2 cycles - timeout threshold)
    "log_file": "humidity_test_results.log",
}


class HumidityTestRunner:
    """Runs automated tests for humidity control feature."""

    def __init__(self, client: Client, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.results = []
        self.test_start_time = None
        self.cycle_min = None  # Will be read from thermostat configuration

    def log_result(self, scenario: str, step: str, passed: bool, message: str, details: Optional[Dict] = None):
        """Log a test result."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "scenario": scenario,
            "step": step,
            "passed": passed,
            "message": message,
            "details": details or {},
        }
        self.results.append(result)

        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {scenario} - {step}: {message}")
        if details:
            logger.debug(f"  Details: {json.dumps(details, indent=2)}")

    async def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of an entity."""
        try:
            state = await self.client.async_get_state(entity_id=entity_id)
            # Convert State object to dict if needed
            if hasattr(state, 'entity_id'):
                return {
                    "entity_id": state.entity_id,
                    "state": state.state,
                    "attributes": state.attributes if hasattr(state, 'attributes') else {},
                }
            return state
        except Exception as e:
            logger.error(f"Error getting state for {entity_id}: {e}")
            return None

    async def get_attribute(self, entity_id: str, attribute_path: str) -> Any:
        """Get a nested attribute from entity state."""
        state = await self.get_state(entity_id)
        if not state:
            return None

        attrs = state.get("attributes", {})
        parts = attribute_path.split(".")
        value = attrs

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    async def call_service(self, domain: str, service: str, entity_id: str, **kwargs):
        """Call a Home Assistant service."""
        try:
            # Build service data with entity_id and any additional kwargs
            service_data = {"entity_id": entity_id, **kwargs}
            await self.client.async_trigger_service(
                domain=domain,
                service=service,
                **service_data
            )
            logger.debug(f"Called {domain}.{service} on {entity_id} with {kwargs}")
        except Exception as e:
            logger.error(f"Error calling {domain}.{service}: {e}")
            raise

    async def wait_for_state(
        self,
        entity_id: str,
        attribute_path: str,
        expected_value: Any,
        timeout: int = None,
        comparison: str = "equals"
    ) -> bool:
        """Wait for an attribute to reach expected value."""
        timeout = timeout or self.config["max_wait_time"]
        start_time = asyncio.get_event_loop().time()
        last_log_time = start_time
        check_interval = 30  # Log progress every 30 seconds

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - start_time
            remaining = timeout - elapsed

            # Log progress every check_interval seconds
            if current_time - last_log_time >= check_interval:
                logger.info(f"  Still waiting... ({elapsed:.0f}s elapsed, {remaining:.0f}s remaining)")
                last_log_time = current_time

            current_value = await self.get_attribute(entity_id, attribute_path)

            if comparison == "equals":
                if current_value == expected_value:
                    logger.info(f"  ✅ Target reached! {attribute_path} = {current_value}")
                    return True
            elif comparison == "greater_than":
                if current_value is not None and current_value > expected_value:
                    logger.info(f"  ✅ Target reached! {attribute_path} = {current_value}")
                    return True
            elif comparison == "less_than":
                if current_value is not None and current_value < expected_value:
                    logger.info(f"  ✅ Target reached! {attribute_path} = {current_value}")
                    return True
            elif comparison == "contains":
                if expected_value in str(current_value):
                    logger.info(f"  ✅ Target reached! {attribute_path} = {current_value}")
                    return True

            await asyncio.sleep(2)  # Check every 2 seconds

        logger.error(f"  ⏱️  TIMEOUT ERROR: Waited {timeout} seconds ({timeout/60:.1f} minutes) but target state not reached")
        logger.error(f"  Expected: {attribute_path} = {expected_value}")
        logger.error(f"  This exceeds the expected wait time (1.5x cycle = {self.config['wait_time']}s). Something may be wrong.")
        return False

    async def setup_initial_conditions(
        self,
        hvac_mode: str = "cool",
        target_temp: float = None,
        humidity: float = None
    ):
        """Set up initial conditions for a test."""
        logger.info(f"Setting up initial conditions: mode={hvac_mode}, temp={target_temp}, humidity={humidity}")

        # Set HVAC mode
        if hvac_mode:
            logger.info(f"  Setting HVAC mode to {hvac_mode}...")
            await self.call_service(
                "climate",
                "set_hvac_mode",
                self.config["thermostat_entity"],
                hvac_mode=hvac_mode
            )
            logger.info(f"  Waiting {self.config['wait_time']} seconds ({self.config['wait_time']/60:.1f} minutes)...")
            await asyncio.sleep(self.config["wait_time"])

        # Set target temperature
        if target_temp is not None:
            logger.info(f"  Setting target temperature to {target_temp}°C...")
            await self.call_service(
                "climate",
                "set_temperature",
                self.config["thermostat_entity"],
                temperature=target_temp
            )
            logger.info(f"  Waiting {self.config['wait_time']} seconds ({self.config['wait_time']/60:.1f} minutes)...")
            await asyncio.sleep(self.config["wait_time"])

        # Set humidity
        if humidity is not None:
            logger.info(f"  Setting humidity to {humidity}%...")
            await self.call_service(
                "input_number",
                "set_value",
                self.config["humidity_sensor"],
                value=humidity
            )
            logger.info(f"  Waiting {self.config['wait_time']} seconds ({self.config['wait_time']/60:.1f} minutes)...")
            await asyncio.sleep(self.config["wait_time"])

    async def test_scenario_1_dry_mode_activation(self):
        """Test Scenario 1: DRY Mode Activation (Humidity High, Temperature at Target)."""
        scenario = "Scenario 1: DRY Mode Activation"
        logger.info(f"\n{'='*60}\n{scenario}\n{'='*60}")

        try:
            # Get current room temperature
            current_temp = await self.get_attribute(
                self.config["thermostat_entity"],
                "current_temperature"
            )
            if current_temp is None:
                self.log_result(
                    scenario, "Setup",
                    False,
                    "Could not get current temperature",
                    {"entity": self.config["thermostat_entity"]}
                )
                return

            # Step 1: Set initial conditions
            await self.setup_initial_conditions(
                hvac_mode="cool",
                target_temp=current_temp,  # Match current temperature
                humidity=55.0  # Below threshold
            )

            # Step 2: Verify initial state
            hvac_mode = await self.get_attribute(
                self.config["thermostat_entity"],
                "hvac_mode"
            )
            if hvac_mode != "cool":
                self.log_result(
                    scenario, "Initial State Check",
                    False,
                    f"Expected COOL mode, got {hvac_mode}",
                    {"expected": "cool", "actual": hvac_mode}
                )
                return

            self.log_result(
                scenario, "Initial State Check",
                True,
                f"Thermostat is in COOL mode",
                {"hvac_mode": hvac_mode}
            )

            # Step 3: Increase humidity above threshold
            logger.info("Increasing humidity above threshold (65.0%)...")
            await self.call_service(
                "input_number",
                "set_value",
                self.config["humidity_sensor"],
                value=65.0
            )
            logger.info(f"Waiting {self.config['wait_time']} seconds for humidity change to register...")
            await asyncio.sleep(self.config["wait_time"])

            # Step 4: Wait for DRY mode activation (wait at least one cycle)
            logger.info("Waiting for DRY mode activation (checking every 2 seconds)...")
            logger.info(f"Maximum wait time: {self.config['max_wait_time']} seconds ({self.config['max_wait_time']/60:.1f} minutes)")
            dry_activated = await self.wait_for_state(
                self.config["thermostat_entity"],
                "hvac_mode",
                "dry",
                timeout=self.config["max_wait_time"]
            )

            if dry_activated:
                # Verify all expected attributes
                hvac_reason = await self.get_attribute(
                    self.config["thermostat_entity"],
                    "specific_states.hvac_reason"
                )
                is_too_high = await self.get_attribute(
                    self.config["thermostat_entity"],
                    "humidity_manager.is_humidity_too_high"
                )
                current_humidity = await self.get_attribute(
                    self.config["thermostat_entity"],
                    "humidity_manager.current_humidity"
                )

                self.log_result(
                    scenario, "DRY Mode Activation",
                    True,
                    "DRY mode activated successfully",
                    {
                        "hvac_mode": "dry",
                        "hvac_reason": hvac_reason,
                        "is_humidity_too_high": is_too_high,
                        "current_humidity": current_humidity,
                    }
                )
            else:
                self.log_result(
                    scenario, "DRY Mode Activation",
                    False,
                    "DRY mode did not activate within timeout",
                    {"timeout": self.config["max_wait_time"]}
                )

        except Exception as e:
            self.log_result(
                scenario, "Error",
                False,
                f"Exception during test: {str(e)}",
                {"exception": str(e)}
            )

    async def test_scenario_2_cool_mode_priority(self):
        """Test Scenario 2: COOL Mode Priority (Humidity High, But Cooling Needed)."""
        scenario = "Scenario 2: COOL Mode Priority"
        logger.info(f"\n{'='*60}\n{scenario}\n{'='*60}")

        try:
            # Start from DRY mode (from Scenario 1)
            current_temp = await self.get_attribute(
                self.config["thermostat_entity"],
                "current_temperature"
            )
            if current_temp is None:
                current_temp = 22.0

            # Ensure we're in DRY mode with high humidity
            await self.setup_initial_conditions(
                hvac_mode="cool",
                target_temp=current_temp,
                humidity=65.0
            )

            # Wait for DRY mode if not already active (wait at least one cycle)
            await asyncio.sleep(self.config["wait_time"])

            # Lower target temperature to require cooling
            target_temp = current_temp - 2.0  # 2°C below current
            await self.call_service(
                "climate",
                "set_temperature",
                self.config["thermostat_entity"],
                temperature=target_temp
            )

            # Wait for COOL mode activation (wait at least one cycle)
            await asyncio.sleep(self.config["wait_time"])
            cool_activated = await self.wait_for_state(
                self.config["thermostat_entity"],
                "hvac_mode",
                "cool",
                timeout=self.config["max_wait_time"]
            )

            if cool_activated:
                hvac_reason = await self.get_attribute(
                    self.config["thermostat_entity"],
                    "specific_states.hvac_reason"
                )
                self.log_result(
                    scenario, "COOL Mode Priority",
                    True,
                    "COOL mode took priority over DRY mode",
                    {
                        "hvac_mode": "cool",
                        "hvac_reason": hvac_reason,
                        "target_temp": target_temp,
                        "current_temp": current_temp,
                    }
                )
            else:
                self.log_result(
                    scenario, "COOL Mode Priority",
                    False,
                    "COOL mode did not activate within timeout",
                    {"timeout": self.config["max_wait_time"]}
                )

        except Exception as e:
            self.log_result(
                scenario, "Error",
                False,
                f"Exception during test: {str(e)}",
                {"exception": str(e)}
            )

    async def test_scenario_3_dry_mode_deactivation(self):
        """Test Scenario 3: DRY Mode Deactivation (Humidity Drops Below Threshold)."""
        scenario = "Scenario 3: DRY Mode Deactivation"
        logger.info(f"\n{'='*60}\n{scenario}\n{'='*60}")

        try:
            # Ensure we're in DRY mode
            current_temp = await self.get_attribute(
                self.config["thermostat_entity"],
                "current_temperature"
            )
            if current_temp is None:
                current_temp = 22.0

            await self.setup_initial_conditions(
                hvac_mode="cool",
                target_temp=current_temp,
                humidity=65.0
            )

            # Wait for DRY mode (wait at least one cycle)
            await asyncio.sleep(self.config["wait_time"])

            # Decrease humidity below threshold
            await self.call_service(
                "input_number",
                "set_value",
                self.config["humidity_sensor"],
                value=55.0
            )

            # Wait for COOL mode activation (wait at least one cycle)
            await asyncio.sleep(self.config["wait_time"])
            cool_activated = await self.wait_for_state(
                self.config["thermostat_entity"],
                "hvac_mode",
                "cool",
                timeout=self.config["max_wait_time"]
            )

            if cool_activated:
                is_too_high = await self.get_attribute(
                    self.config["thermostat_entity"],
                    "humidity_manager.is_humidity_too_high"
                )
                self.log_result(
                    scenario, "DRY Mode Deactivation",
                    True,
                    "DRY mode deactivated when humidity dropped",
                    {
                        "hvac_mode": "cool",
                        "is_humidity_too_high": is_too_high,
                    }
                )
            else:
                self.log_result(
                    scenario, "DRY Mode Deactivation",
                    False,
                    "COOL mode did not activate within timeout",
                    {"timeout": self.config["max_wait_time"]}
                )

        except Exception as e:
            self.log_result(
                scenario, "Error",
                False,
                f"Exception during test: {str(e)}",
                {"exception": str(e)}
            )

    async def test_scenario_4_temperature_threshold(self):
        """Test Scenario 4: Temperature Threshold Boundary Test."""
        scenario = "Scenario 4: Temperature Threshold"
        logger.info(f"\n{'='*60}\n{scenario}\n{'='*60}")

        try:
            base_temp = 22.0
            await self.setup_initial_conditions(
                hvac_mode="cool",
                target_temp=base_temp,
                humidity=65.0
            )

            # Test Part A: Temperature at target (0.0°C difference) - Should use DRY
            logger.info("Part A: Setting temperature to target (22.0°C)...")
            await self.call_service(
                "climate",
                "set_temperature",
                self.config["thermostat_entity"],
                temperature=base_temp
            )
            logger.info(f"Waiting {self.config['wait_time']} seconds for thermostat to react...")
            await asyncio.sleep(self.config["wait_time"])

            logger.info("Checking HVAC mode...")
            hvac_mode = await self.get_attribute(
                self.config["thermostat_entity"],
                "hvac_mode"
            )
            self.log_result(
                scenario, "Part A: Temp at target",
                hvac_mode == "dry",
                f"Temperature at target (0.0°C diff), mode: {hvac_mode}",
                {"expected": "dry", "actual": hvac_mode}
            )

            # Test Part B: Temperature just below threshold (0.05°C difference) - Should use DRY
            logger.info("Part B: Setting temperature to 21.95°C (0.05°C below target)...")
            await self.call_service(
                "climate",
                "set_temperature",
                self.config["thermostat_entity"],
                temperature=base_temp - 0.05
            )
            logger.info(f"Waiting {self.config['wait_time']} seconds for thermostat to react...")
            await asyncio.sleep(self.config["wait_time"])

            logger.info("Checking HVAC mode...")
            hvac_mode = await self.get_attribute(
                self.config["thermostat_entity"],
                "hvac_mode"
            )
            self.log_result(
                scenario, "Part B: Temp within 0.1°C",
                hvac_mode == "dry",
                f"Temperature within 0.1°C threshold, mode: {hvac_mode}",
                {"expected": "dry", "actual": hvac_mode}
            )

            # Test Part C: Temperature above threshold (0.2°C difference) - Should use COOL
            logger.info("Part C: Setting temperature to 21.8°C (0.2°C below target, requires cooling)...")
            await self.call_service(
                "climate",
                "set_temperature",
                self.config["thermostat_entity"],
                temperature=base_temp - 0.2
            )
            logger.info(f"Waiting {self.config['wait_time']} seconds for thermostat to react...")
            await asyncio.sleep(self.config["wait_time"])

            logger.info("Checking HVAC mode...")
            hvac_mode = await self.get_attribute(
                self.config["thermostat_entity"],
                "hvac_mode"
            )
            self.log_result(
                scenario, "Part C: Temp above 0.1°C",
                hvac_mode == "cool",
                f"Temperature above 0.1°C threshold, mode: {hvac_mode}",
                {"expected": "cool", "actual": hvac_mode}
            )

        except Exception as e:
            self.log_result(
                scenario, "Error",
                False,
                f"Exception during test: {str(e)}",
                {"exception": str(e)}
            )

    async def test_scenario_5_non_cool_mode_ignored(self):
        """Test Scenario 5: Non-COOL Mode Ignored."""
        scenario = "Scenario 5: Non-COOL Mode Ignored"
        logger.info(f"\n{'='*60}\n{scenario}\n{'='*60}")

        try:
            # Set to HEAT mode with high humidity
            await self.setup_initial_conditions(
                hvac_mode="heat",
                humidity=70.0
            )

            # Wait at least one cycle to ensure state is stable
            await asyncio.sleep(self.config["wait_time"])

            hvac_mode = await self.get_attribute(
                self.config["thermostat_entity"],
                "hvac_mode"
            )
            is_too_high = await self.get_attribute(
                self.config["thermostat_entity"],
                "humidity_manager.is_humidity_too_high"
            )

            self.log_result(
                scenario, "HEAT Mode Ignored",
                hvac_mode == "heat",
                f"Humidity control does not interfere with HEAT mode",
                {
                    "hvac_mode": hvac_mode,
                    "is_humidity_too_high": is_too_high,
                }
            )

        except Exception as e:
            self.log_result(
                scenario, "Error",
                False,
                f"Exception during test: {str(e)}",
                {"exception": str(e)}
            )

    async def verify_configuration(self) -> bool:
        """Verify test configuration is valid."""
        logger.info("Verifying test configuration...")

        # Check thermostat entity exists
        thermostat_state = await self.get_state(self.config["thermostat_entity"])
        if not thermostat_state:
            logger.error(f"Thermostat entity not found: {self.config['thermostat_entity']}")
            return False

        # Get cycle_min from thermostat configuration
        cycle_min = await self.get_attribute(
            self.config["thermostat_entity"],
            "configuration.cycle_min"
        )
        if cycle_min is None:
            # Fallback to default if not found
            cycle_min = 5
            logger.warning(f"Could not read cycle_min from thermostat, using default: {cycle_min} minutes")
        else:
            logger.info(f"Thermostat cycle time: {cycle_min} minutes")

        self.cycle_min = cycle_min

        # Calculate wait times based on cycle_min to prevent short cycling
        cycle_seconds = cycle_min * 60
        if self.config["wait_time"] is None:
            self.config["wait_time"] = int(cycle_seconds * self.config.get("cycle_multiplier", 1.5))
            logger.info(f"Calculated wait_time: {self.config['wait_time']} seconds ({self.config['wait_time']/60:.1f} minutes)")

        if self.config["max_wait_time"] is None:
            # Use 2x cycle time as timeout - if it takes longer, something is wrong
            self.config["max_wait_time"] = int(cycle_seconds * 2)  # 2 cycles max wait (timeout)
            logger.info(f"Calculated max_wait_time: {self.config['max_wait_time']} seconds ({self.config['max_wait_time']/60:.1f} minutes) - timeout threshold")

        # Check humidity sensor exists
        humidity_state = await self.get_state(self.config["humidity_sensor"])
        if not humidity_state:
            logger.error(f"Humidity sensor not found: {self.config['humidity_sensor']}")
            return False

        # Check thermostat has humidity feature configured
        is_configured = await self.get_attribute(
            self.config["thermostat_entity"],
            "is_humidity_configured"
        )
        if not is_configured:
            logger.error("Humidity feature is not configured on thermostat")
            return False

        # Check DRY mode is available
        hvac_modes = await self.get_attribute(
            self.config["thermostat_entity"],
            "hvac_modes"
        )
        if "dry" not in hvac_modes:
            logger.error("DRY mode is not available in thermostat HVAC modes")
            return False

        logger.info("✅ Configuration verified successfully")
        logger.info(f"⚠️  Wait times configured to prevent short cycling (cycle time: {cycle_min} min)")
        return True

    async def run_all_tests(self):
        """Run all test scenarios."""
        self.test_start_time = datetime.now()
        logger.info(f"\n{'='*60}")
        logger.info("Starting Humidity Control Feature Tests")
        logger.info(f"Test started at: {self.test_start_time.isoformat()}")
        logger.info(f"{'='*60}\n")

        # Verify configuration
        if not await self.verify_configuration():
            logger.error("Configuration verification failed. Please check your setup.")
            return

        # Run test scenarios
        await self.test_scenario_1_dry_mode_activation()
        await asyncio.sleep(self.config["wait_time"])

        await self.test_scenario_2_cool_mode_priority()
        await asyncio.sleep(self.config["wait_time"])

        await self.test_scenario_3_dry_mode_deactivation()
        await asyncio.sleep(self.config["wait_time"])

        await self.test_scenario_4_temperature_threshold()
        await asyncio.sleep(self.config["wait_time"])

        await self.test_scenario_5_non_cool_mode_ignored()

        # Generate summary
        self.generate_summary()

    def save_results(self):
        """Save test results to log file (can be called on interruption)."""
        if not self.results:
            logger.info("No test results to save.")
            return

        if self.test_start_time is None:
            self.test_start_time = datetime.now()

        self.generate_summary()

    def generate_summary(self):
        """Generate test summary and write to log file."""
        test_end_time = datetime.now()
        if self.test_start_time is None:
            self.test_start_time = datetime.now()
        duration = (test_end_time - self.test_start_time).total_seconds()

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        failed_tests = total_tests - passed_tests

        summary = {
            "test_start": self.test_start_time.isoformat(),
            "test_end": test_end_time.isoformat(),
            "duration_seconds": duration,
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%",
            "results": self.results,
            "interrupted": True if total_tests > 0 and test_end_time < datetime.now() else False,
        }

        # Write to log file
        log_file = self.config["log_file"]
        with open(log_file, "w") as f:
            json.dump(summary, f, indent=2)

        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Pass Rate: {summary['pass_rate']}")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"Results saved to: {log_file}")
        logger.info(f"{'='*60}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run humidity control feature tests")
    parser.add_argument(
        "--url",
        default=os.getenv("HASS_URL", "http://localhost:8123"),
        help="Home Assistant URL (default: http://localhost:8123)"
    )
    parser.add_argument(
        "--token",
        default=os.getenv("HASS_TOKEN"),
        help="Home Assistant access token (or set HASS_TOKEN env var)"
    )
    parser.add_argument(
        "--thermostat",
        help="Thermostat entity ID (overrides config)"
    )
    parser.add_argument(
        "--humidity-sensor",
        help="Humidity sensor entity ID (overrides config)"
    )
    parser.add_argument(
        "--log-file",
        help="Log file path (overrides config)"
    )

    args = parser.parse_args()

    if not args.token:
        logger.error("HASS_TOKEN environment variable or --token argument required")
        sys.exit(1)

    # Merge config with command line arguments
    config = DEFAULT_CONFIG.copy()
    if args.thermostat:
        config["thermostat_entity"] = args.thermostat
    if args.humidity_sensor:
        config["humidity_sensor"] = args.humidity_sensor
    if args.log_file:
        config["log_file"] = args.log_file

    runner = None
    try:
        # Connect to Home Assistant
        # Ensure URL ends with /api if not already present
        api_url = args.url.rstrip('/')
        if not api_url.endswith('/api'):
            api_url = f"{api_url}/api"

        logger.info(f"Connecting to Home Assistant at {api_url}...")
        # Use async mode for async methods and use as context manager
        async with Client(api_url, args.token, use_async=True) as client:
            # Create test runner
            runner = HumidityTestRunner(client, config)

            # Run tests
            await runner.run_all_tests()

    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrupted by user (Ctrl-C)")
        if runner is not None:
            logger.info("Saving partial results...")
            try:
                runner.save_results()
            except Exception as e:
                logger.error(f"Error saving results: {e}")
        else:
            logger.info("No test results to save (interrupted before tests started).")
        sys.exit(130)  # Standard exit code for Ctrl-C
    except UnauthorizedError:
        logger.error("Authentication failed. Check your access token.")
        sys.exit(1)
    except RequestError as e:
        logger.error(f"Cannot connect to Home Assistant at {args.url}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
