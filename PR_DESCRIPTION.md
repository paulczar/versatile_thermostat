# Add Humidity Control Feature with Automatic DRY Mode Switching

## Problem Statement

In high-humidity climates and regions, air conditioning systems provide cooling that naturally dehumidifies the air while running. However, when the target temperature is reached and the AC stops running, humidity levels can quickly rise again, making the space feel uncomfortable despite the correct temperature being maintained.

**The Core Issue:**
- AC cooling naturally dehumidifies while actively running
- When temperature reaches target, the AC stops running
- Humidity can remain high (60%+ relative humidity)
- Space feels "muggy" or "sticky" even at correct temperature
- Users may unnecessarily lower temperature setpoint to keep AC running, wasting energy

**Why This Matters:**
- Human comfort depends on both temperature AND humidity levels
- High humidity reduces the effectiveness of evaporative cooling from skin
- Can lead to overcooling and significantly higher energy consumption
- Particularly problematic in tropical, subtropical, and coastal climates
- Common issue in basements and naturally humid environments

## Solution

This PR adds automatic humidity control that switches the AC to DRY mode when:
- Temperature is at or near target (cooling not actively needed)
- Humidity exceeds a configurable threshold (default: 60%)
- AC is in COOL mode
- The underlying AC device supports DRY mode

**Key Features:**
- **Automatic Mode Switching**: Seamlessly switches between COOL and DRY modes based on conditions
- **Cooling Priority**: COOL mode always overrides DRY when temperature control is needed
- **Energy Efficient**: DRY mode uses less energy than active cooling
- **Configurable Threshold**: Adjustable per thermostat (default 60%)
- **Sensor Flexibility**: Works with any humidity sensor or input_number entity

## How It Works

1. **Monitoring**: Continuously monitors humidity via configured sensor entity
2. **Threshold Check**: Compares current humidity to user-defined threshold
3. **Cooling Need Assessment**: Uses proportional algorithm's `on_percent <= 0.05` to determine if active cooling is needed
4. **Mode Switching**:
   - If humidity > threshold AND cooling not needed → switch to DRY mode
   - If temperature rises and cooling needed → switch back to COOL mode
5. **Priority System**: Temperature control always takes precedence over humidity control

## Technical Implementation

**New Components:**
- `FeatureHumidityManager`: Manages humidity monitoring and threshold checking
- Config flow integration: Humidity sensor selection and threshold configuration
- State manager integration: DRY mode switching logic in HVAC mode calculation
- Central configuration support: Shared threshold across multiple thermostats

**Integration Points:**
- Integrated into `BaseThermostat` following existing feature manager pattern
- State manager checks humidity after window/auto-start-stop but before final mode assignment
- Cooling override uses proportional algorithm's `on_percent` to determine active cooling need

**Configuration:**
- Enable in Features step: "Use humidity management"
- Configure in Humidity management step:
  - Select humidity sensor entity
  - Set humidity threshold (default: 60%)
  - Option to use central configuration

## Use Cases

1. **Tropical Climates**: Maintain comfort when temperature is at target but humidity is high
2. **Coastal Areas**: Address high ambient humidity levels
3. **Basements**: Control humidity in naturally damp spaces
4. **Energy Efficiency**: Use DRY mode instead of overcooling to reduce humidity

## Testing

- ✅ Unit tests for `FeatureHumidityManager` (10 test cases)
- ✅ State manager integration tests (8 scenarios)
- ✅ Covers: threshold checking, sensor changes, cooling override, edge cases
- ✅ All tests passing

## Documentation

- ✅ Feature documentation: `documentation/en/feature-humidity.md`
- ✅ Testing guide: `TESTING_HUMIDITY.md`
- ✅ Updated README and base-attributes documentation
- ✅ Translation support: English translations included

## Compatibility

- Only available for AC mode thermostats (`over_climate` type)
- Requires underlying AC device to support DRY mode
- Backward compatible: Existing configurations unaffected
- Optional feature: Must be explicitly enabled

## Benefits

1. **Improved Comfort**: Better comfort in high-humidity conditions without overcooling
2. **Energy Savings**: More efficient than running AC just for dehumidification
3. **Automatic Operation**: No manual intervention required
4. **Flexible Configuration**: Per-thermostat threshold configuration
5. **Maintains Priority**: Temperature control always takes precedence

---

This feature addresses a common comfort issue in humid climates where temperature alone doesn't ensure comfort. By automatically switching to DRY mode when appropriate, users can maintain comfort without overcooling, resulting in better comfort and energy efficiency.
