# pylint: disable=wildcard-import, unused-wildcard-import, protected-access, unused-argument, line-too-long

"""Test the Humidity Feature Manager"""
import logging
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock

from custom_components.versatile_thermostat.base_thermostat import BaseThermostat
from custom_components.versatile_thermostat.feature_humidity_manager import (
    FeatureHumidityManager,
)

from .commons import *

logging.getLogger().setLevel(logging.DEBUG)


@pytest.mark.parametrize(
    "humidity_value, threshold, is_too_high",
    [
        (65.0, 60.0, True),
        (55.0, 60.0, False),
        (60.0, 60.0, False),  # Equal to threshold, not too high
        (60.1, 60.0, True),  # Just above threshold
        (None, 60.0, False),  # No humidity reading
    ],
)
async def test_humidity_feature_manager(hass: HomeAssistant, humidity_value, threshold, is_too_high):
    """Test the FeatureHumidityManager class directly"""

    fake_vtherm = MagicMock(spec=BaseThermostat)
    type(fake_vtherm).name = PropertyMock(return_value="the name")

    # 1. creation
    humidity_manager = FeatureHumidityManager(fake_vtherm, hass)

    assert humidity_manager is not None
    assert humidity_manager.is_configured is False
    assert humidity_manager.current_humidity is None
    assert humidity_manager.humidity_threshold == 60.0  # Default
    assert humidity_manager.is_humidity_too_high is False
    assert humidity_manager.name == "the name"

    assert len(humidity_manager._active_listener) == 0

    custom_attributes = {}
    humidity_manager.add_custom_attributes(custom_attributes)
    assert custom_attributes["is_humidity_configured"] is False
    assert custom_attributes.get("humidity_manager") is None

    # 2. post_init
    humidity_manager.post_init(
        {
            CONF_HUMIDITY_SENSOR: "sensor.the_humidity_sensor",
            CONF_HUMIDITY_THRESHOLD: threshold,
            CONF_USE_HUMIDITY_FEATURE: True,
        }
    )

    assert humidity_manager.is_configured is True
    assert humidity_manager.current_humidity is None
    assert humidity_manager.humidity_threshold == threshold
    assert humidity_manager.humidity_sensor_entity_id == "sensor.the_humidity_sensor"

    custom_attributes = {}
    humidity_manager.add_custom_attributes(custom_attributes)
    assert custom_attributes["is_humidity_configured"] is True
    assert custom_attributes["humidity_manager"]["humidity_sensor_entity_id"] == "sensor.the_humidity_sensor"
    assert custom_attributes["humidity_manager"]["current_humidity"] is None
    assert custom_attributes["humidity_manager"]["humidity_threshold"] == threshold

    # 3. start listening
    await humidity_manager.start_listening()
    assert humidity_manager.is_configured is True

    assert len(humidity_manager._active_listener) == 1

    # 4. test refresh with humidity value
    with patch(
        "homeassistant.core.StateMachine.get",
        return_value=State("sensor.the_humidity_sensor", str(humidity_value) if humidity_value is not None else STATE_UNAVAILABLE),
    ), patch(
        "custom_components.versatile_thermostat.feature_humidity_manager.get_safe_float",
        return_value=humidity_value,
    ):
        fake_vtherm.update_states = AsyncMock()
        fake_vtherm.requested_state = MagicMock()
        fake_vtherm.requested_state.force_changed = MagicMock()

        ret = await humidity_manager.refresh_state()
        assert humidity_manager.is_configured is True
        assert humidity_manager.current_humidity == humidity_value
        assert humidity_manager.is_humidity_too_high == is_too_high

        if humidity_value is not None:
            assert ret is True  # Changed from None
        else:
            assert ret is False  # No change

    # 5. test sensor change event
    fake_vtherm.update_states = AsyncMock()
    fake_vtherm.requested_state = MagicMock()
    fake_vtherm.requested_state.force_changed = MagicMock()

    old_humidity = humidity_manager.current_humidity
    new_humidity = 70.0 if humidity_value != 70.0 else 50.0

    with patch(
        "custom_components.versatile_thermostat.feature_humidity_manager.get_safe_float",
        return_value=new_humidity,
    ):
        await humidity_manager._humidity_sensor_changed(
            event=Event(
                event_type=EVENT_STATE_CHANGED,
                data={
                    "entity_id": "sensor.the_humidity_sensor",
                    "new_state": State("sensor.the_humidity_sensor", str(new_humidity)),
                    "old_state": State("sensor.the_humidity_sensor", str(old_humidity) if old_humidity is not None else STATE_UNAVAILABLE),
                },
            )
        )

        assert humidity_manager.current_humidity == new_humidity
        assert fake_vtherm.requested_state.force_changed.called
        fake_vtherm.update_states.assert_called_once_with(force=True)

    humidity_manager.stop_listening()
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    "use_humidity_feature, humidity_sensor_entity_id, threshold, is_configured",
    [
        (True, "sensor.the_humidity_sensor", 60.0, True),
        (True, "sensor.the_humidity_sensor", 70.0, True),
        (False, "sensor.the_humidity_sensor", 60.0, False),
        (True, None, 60.0, False),
        (True, "sensor.the_humidity_sensor", None, True),  # Uses default threshold
    ],
)
async def test_humidity_feature_manager_post_init(
    hass: HomeAssistant,
    use_humidity_feature,
    humidity_sensor_entity_id,
    threshold,
    is_configured,
):
    """Test the FeatureHumidityManager post_init with various configurations"""

    fake_vtherm = MagicMock(spec=BaseThermostat)
    type(fake_vtherm).name = PropertyMock(return_value="the name")

    humidity_manager = FeatureHumidityManager(fake_vtherm, hass)
    assert humidity_manager is not None

    config = {
        CONF_USE_HUMIDITY_FEATURE: use_humidity_feature,
        CONF_HUMIDITY_SENSOR: humidity_sensor_entity_id,
    }
    if threshold is not None:
        config[CONF_HUMIDITY_THRESHOLD] = threshold

    humidity_manager.post_init(config)

    assert humidity_manager.is_configured is is_configured
    assert humidity_manager.humidity_sensor_entity_id == humidity_sensor_entity_id
    if threshold is not None:
        assert humidity_manager.humidity_threshold == threshold
    else:
        assert humidity_manager.humidity_threshold == 60.0  # Default


@pytest.mark.parametrize(
    "is_configured, requested_mode, hvac_modes_include_dry, is_humidity_too_high, current_temp, target_temp, expected_result",
    [
        # Not configured -> False
        (False, VThermHvacMode_COOL, True, True, 25.0, 22.0, False),
        # Not COOL mode -> False
        (True, VThermHvacMode_HEAT, True, True, 25.0, 22.0, False),
        # DRY mode not available -> False
        (True, VThermHvacMode_COOL, False, True, 25.0, 22.0, False),
        # Humidity OK -> False
        (True, VThermHvacMode_COOL, True, False, 25.0, 22.0, False),
        # Humidity too high, cooling needed (temp > target + 0.1) -> False
        (True, VThermHvacMode_COOL, True, True, 25.0, 22.0, False),
        # Humidity too high, cooling not needed (temp <= target + 0.1) -> True
        (True, VThermHvacMode_COOL, True, True, 22.0, 22.0, True),
        (True, VThermHvacMode_COOL, True, True, 22.05, 22.0, True),  # Within 0.1°C threshold
        (True, VThermHvacMode_COOL, True, True, 22.2, 22.0, False),  # Above 0.1°C threshold
        # Missing temperature -> False
        (True, VThermHvacMode_COOL, True, True, None, 22.0, False),
        (True, VThermHvacMode_COOL, True, True, 25.0, None, False),
    ],
)
async def test_should_use_dry_mode(
    hass: HomeAssistant,
    is_configured: bool,
    requested_mode,
    hvac_modes_include_dry: bool,
    is_humidity_too_high: bool,
    current_temp: float | None,
    target_temp: float | None,
    expected_result: bool,
):
    """Test the should_use_dry_mode method"""
    from custom_components.versatile_thermostat.vtherm_hvac_mode import VThermHvacMode_COOL, VThermHvacMode_DRY

    fake_vtherm = MagicMock(spec=BaseThermostat)
    type(fake_vtherm).name = PropertyMock(return_value="the name")
    type(fake_vtherm).current_temperature = PropertyMock(return_value=current_temp)
    type(fake_vtherm).target_temperature = PropertyMock(return_value=target_temp)

    hvac_modes = [VThermHvacMode_COOL]
    if hvac_modes_include_dry:
        hvac_modes.append(VThermHvacMode_DRY)
    type(fake_vtherm).vtherm_hvac_modes = PropertyMock(return_value=hvac_modes)

    humidity_manager = FeatureHumidityManager(fake_vtherm, hass)
    humidity_manager._is_configured = is_configured
    humidity_manager._current_humidity = 65.0 if is_humidity_too_high else 50.0
    humidity_manager._humidity_threshold = 60.0

    result = humidity_manager.should_use_dry_mode(requested_mode)
    assert result == expected_result
