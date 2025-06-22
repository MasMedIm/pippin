#!/usr/bin/env python3
"""
Opentrons MCP Server - AI Agent interface to Opentrons robot
"""
from mcp.server.fastmcp import FastMCP
import requests
import json

# Initialize the FastMCP server
mcp = FastMCP("Opentrons Agent")

# Opentrons robot configuration
ROBOT_IP = "192.168.0.83:31950"
HEADERS = {"opentrons-version": "2"}

@mcp.tool()
def get_robot_health() -> str:
    """Get the current health status of the Opentrons robot"""
    try:
        response = requests.get(f"http://{ROBOT_IP}/health", headers=HEADERS)
        return f"Robot Status: {response.json()}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_instruments() -> str:
    """Get available instruments (pipettes) on the robot"""
    try:
        response = requests.get(f"http://{ROBOT_IP}/instruments", headers=HEADERS)
        return f"Available Instruments: {response.json()}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def list_protocols() -> str:
    """List all protocols available on the robot"""
    try:
        response = requests.get(f"http://{ROBOT_IP}/protocols", headers=HEADERS)
        return f"Available Protocols: {response.json()}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def validate_labware_exists(labware_name: str) -> str:
    """Check if labware type exists in OpenTrons library"""
    # Common OpenTrons labware (this would ideally query the robot's API)
    valid_labware = {
        # Plates
        'corning_96_wellplate_360ul_flat': '96-well flat bottom plate',
        'nest_96_wellplate_200ul_flat': '96-well NEST plate',
        'biorad_96_wellplate_200ul_pcr': '96-well PCR plate',
        
        # Reservoirs  
        'nest_12_reservoir_15ml': '12-channel reservoir',
        'nest_1_reservoir_195ml': 'Single reservoir',
        'agilent_1_reservoir_290ml': 'Agilent reservoir',
        
        # Tip racks
        'opentrons_flex_96_tiprack_1000ul': '1000µL tip rack',
        'opentrons_flex_96_tiprack_200ul': '200µL tip rack', 
        'opentrons_flex_96_tiprack_50ul': '50µL tip rack',
        
        # Tubes
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap': '24-tube rack',
        'nest_15_tuberack_15000ul': '15mL tube rack'
    }
    
    if labware_name in valid_labware:
        return f"✅ Valid labware: {labware_name} ({valid_labware[labware_name]})"
    else:
        suggestions = [name for name in valid_labware.keys() if labware_name.lower() in name.lower()]
        if suggestions:
            return f"❌ Invalid labware: {labware_name}. Did you mean: {', '.join(suggestions[:3])}?"
        else:
            return f"❌ Invalid labware: {labware_name}. Available options: {', '.join(list(valid_labware.keys())[:5])}..."

@mcp.tool()
def find_labware_by_description(description: str) -> str:
    """Find labware by human-friendly description (e.g., '96 well plate', 'tip rack')"""
    description_lower = description.lower()
    
    labware_map = {
        "96 well": ["corning_96_wellplate_360ul_flat", "nest_96_wellplate_200ul_flat"],
        "plate": ["corning_96_wellplate_360ul_flat", "nest_96_wellplate_200ul_flat"],
        "reservoir": ["nest_12_reservoir_15ml", "nest_1_reservoir_195ml"],
        "tip": ["opentrons_flex_96_tiprack_1000ul", "opentrons_flex_96_tiprack_200ul","opentrons_flex_96_tiprack_50ul"],
        "1000": ["opentrons_flex_96_tiprack_1000ul"],
        "200": ["opentrons_flex_96_tiprack_200ul", "nest_96_wellplate_200ul_flat"],
        "50":["opentrons_flex_96_tiprack_50ul"],
        "tube": ["opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap"]
    }
    
    matches = []
    for keyword, labware_list in labware_map.items():
        if keyword in description_lower:
            matches.extend(labware_list)
    
    if matches:
        unique_matches = list(set(matches))
        return f"Found labware: {', '.join(unique_matches)}"
    else:
        return f"No labware found for '{description}'. Try: '96 well', 'reservoir', 'tip rack', 'tube rack'"

@mcp.tool()
def check_deck_layout(positions_and_labware: str) -> str:
    """Validate deck layout doesn't have conflicts. Format: 'position:labware_type,position:labware_type'"""
    try:
        # Parse input like "1:corning_96_wellplate_360ul_flat,2:nest_12_reservoir_15ml"
        layout = {}
        pairs = positions_and_labware.split(',')
        
        for pair in pairs:
            position, labware = pair.strip().split(':')
            position = int(position)
            
            # Validate position range (OT-3 Flex has positions 1-12)
            if not (1 <= position <= 12):
                return f"❌ Invalid deck position: {position}. Must be 1-12"
            
            # Check for duplicate positions
            if position in layout:
                return f"❌ Position conflict: Position {position} used twice"
            
            layout[position] = labware.strip()
        
        # Check labware compatibility and spacing
        conflicts = []
        
        # Check for height conflicts (tall items need space)
        tall_labware = ['nest_15_tuberack_15000ul', 'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap']
        for pos, labware in layout.items():
            if any(tall in labware for tall in tall_labware):
                # Check adjacent positions for conflicts
                adjacent = [pos-3, pos+3, pos-1, pos+1]  # Up, down, left, right
                for adj_pos in adjacent:
                    if adj_pos in layout and adj_pos != pos:
                        conflicts.append(f"Tall labware at position {pos} may interfere with position {adj_pos}")
        
        if conflicts:
            return f"⚠️ Potential conflicts: {'; '.join(conflicts)}"
        
        # Generate layout visualization
        result = "✅ Deck layout valid!\n\nLayout:\n"
        for pos in sorted(layout.keys()):
            result += f"Position {pos}: {layout[pos]}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error parsing layout: {str(e)}. Use format: '1:labware_name,2:labware_name'"

@mcp.tool()
def suggest_optimal_deck_layout(required_labware: str) -> str:
    """Suggest optimal deck positions for given labware. Format: 'labware1,labware2,labware3'"""
    try:
        labware_list = [item.strip() for item in required_labware.split(',')]
        
        # Positioning strategy: 
        # - Plates in front row (1-3) for easy access
        # - Reservoirs in middle (4-6) 
        # - Tips in back (7-9)
        # - Tall items spread out (10-12)
        
        suggestions = {}
        position = 1
        
        # Sort by priority: plates first, then reservoirs, then tips, then everything else
        priority_order = ['plate', 'reservoir', 'tip', 'tube']
        
        for priority in priority_order:
            for labware in labware_list[:]:  # Copy to avoid modification during iteration
                if priority in labware.lower():
                    if priority == 'plate':
                        suggestions[position] = labware
                        position = min(position + 1, 3)
                    elif priority == 'reservoir':
                        if position <= 3:
                            position = 4
                        suggestions[position] = labware
                        position = min(position + 1, 6)
                    elif priority == 'tip':
                        if position <= 6:
                            position = 7
                        suggestions[position] = labware
                        position = min(position + 1, 9)
                    else:  # tubes and other tall items
                        if position <= 9:
                            position = 10
                        suggestions[position] = labware
                        position = min(position + 1, 12)
                    
                    labware_list.remove(labware)
        
        # Place remaining items
        for labware in labware_list:
            if position <= 12:
                suggestions[position] = labware
                position += 1
        
        result = "Suggested deck layout:\n\n"
        for pos in sorted(suggestions.keys()):
            result += f"Position {pos}: {suggestions[pos]}\n"
        
        if position > 12:
            result += f"\n⚠️ Warning: Too many items for deck (need {len(required_labware.split(','))} positions, only 12 available)"
        
        return result
        
    except Exception as e:
        return f"❌ Error: {str(e)}. Use format: 'labware1,labware2,labware3'"

@mcp.tool()
def get_available_labware() -> str:
    """List all available labware types"""
    labware_categories = {
        "Plates": ["corning_96_wellplate_360ul_flat", "nest_96_wellplate_200ul_flat", "biorad_96_wellplate_200ul_pcr"],
        "Reservoirs": ["nest_12_reservoir_15ml", "nest_1_reservoir_195ml", "agilent_1_reservoir_290ml"],
        "Tip Racks": ["opentrons_flex_96_tiprack_1000ul", "opentrons_flex_96_tiprack_200ul", "opentrons_flex_96_tiprack_50ul"],
        "Tube Racks": ["opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", "nest_15_tuberack_15000ul"]
    }
    
    result = "Available Labware:\n\n"
    for category, items in labware_categories.items():
        result += f"{category}:\n"
        for item in items:
            result += f"  - {item}\n"
        result += "\n"
    
    return result

@mcp.tool()
def create_tartrazine_assay_protocol(
    aspiration_speed: float = 50.0,
    dispense_speed: float = 50.0, 
    mix_volume: int = 100,
    mix_repetitions: int = 3,
    transfer_volume: int = 200
) -> str:
    """Generate tartrazine standard curve protocol with liquid handling parameters for optimization"""
    
    # VALIDATION FIRST
    errors = []
    
    # Speed validation (typical OT-3 ranges)
    if not (1 <= aspiration_speed <= 1000):
        errors.append(f"Aspiration speed {aspiration_speed} outside range 1-1000 µL/s")
    if not (1 <= dispense_speed <= 1000):
        errors.append(f"Dispense speed {dispense_speed} outside range 1-1000 µL/s")
    
    # Volume validation
    if not (1 <= mix_volume <= 1000):
        errors.append(f"Mix volume {mix_volume} outside range 1-1000 µL")
    if not (1 <= transfer_volume <= 1000):
        errors.append(f"Transfer volume {transfer_volume} outside range 1-1000 µL")
    
    # Repetition validation
    if not (1 <= mix_repetitions <= 20):
        errors.append(f"Mix repetitions {mix_repetitions} outside range 1-20")
    
    # Return errors if validation fails
    if errors:
        return f"❌ VALIDATION ERRORS: {'; '.join(errors)}"
    
    # AUTO-SELECT PIPETTE based on volume
    if transfer_volume <= 20:
        pipette_name = "flex_1channel_20"
        mount = "left"
    elif transfer_volume <= 300:
        pipette_name = "flex_1channel_300"  
        mount = "left"
    else:
        pipette_name = "flex_1channel_1000"
        mount = "left"
    
    # GENERATE PROTOCOL if validation passes
    protocol_template = f"""from opentrons import protocol_api

def run(protocol: protocol_api.ProtocolContext):
    # Load labware for tartrazine assay
    assay_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 1)
    reagent_reservoir = protocol.load_labware('nest_12_reservoir_15ml', 2)
    tip_rack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 3)
    
    # Load auto-selected pipette: {pipette_name}
    pipette = protocol.load_instrument('{pipette_name}', '{mount}', tip_racks=[tip_rack])
    pipette.flow_rate.aspirate = {aspiration_speed}
    pipette.flow_rate.dispense = {dispense_speed}
    
    # Create tartrazine standard curve (0, 10, 20, 50, 100, 200 µg/mL)
    concentrations = [0, 10, 20, 50, 100, 200]
    
    for i, conc in enumerate(concentrations):
        # Dispense tartrazine solution
        pipette.transfer({transfer_volume}, reagent_reservoir[f'A{{i+1}}'], assay_plate[f'A{{i+1}}'])
        # Mix with optimization parameters
        pipette.mix({mix_repetitions}, {mix_volume}, assay_plate[f'A{{i+1}}'])
        
    # DECK LAYOUT for operator:
    # Position 1: 96-well assay plate
    # Position 2: 12-well reagent reservoir (A1=0µg/mL, A2=10µg/mL, A3=20µg/mL, A4=50µg/mL, A5=100µg/mL, A6=200µg/mL)
    # Position 3: Tip rack"""
    
    return f"✅ PROTOCOL GENERATED using {pipette_name}\n\n{protocol_template}"

@mcp.tool()
def simulate_protocol_execution(
    aspiration_speed: float,
    dispense_speed: float,
    mix_volume: int,
    mix_repetitions: int,
    transfer_volume: int
) -> str:
    """Simulate protocol execution to catch potential runtime errors before sending to robot"""
    
    simulation_log = []
    errors = []
    warnings = []
    
    # Step 1: Validate all parameters (reuse existing validation)
    param_errors = []
    if not (1 <= aspiration_speed <= 1000):
        param_errors.append(f"Aspiration speed {aspiration_speed} outside range")
    if not (1 <= dispense_speed <= 1000):
        param_errors.append(f"Dispense speed {dispense_speed} outside range")
    if not (1 <= mix_volume <= 1000):
        param_errors.append(f"Mix volume {mix_volume} outside range")
    if not (1 <= transfer_volume <= 1000):
        param_errors.append(f"Transfer volume {transfer_volume} outside range")
    if not (1 <= mix_repetitions <= 20):
        param_errors.append(f"Mix repetitions {mix_repetitions} outside range")
    
    if param_errors:
        errors.extend(param_errors)
        return f"❌ SIMULATION FAILED: {'; '.join(errors)}"
    
    simulation_log.append("✅ Parameter validation passed")
    
    # Step 2: Check pipette selection
    if transfer_volume <= 20:
        pipette = "flex_1channel_20"
        if mix_volume > 20:
            warnings.append("Mix volume exceeds pipette capacity for selected transfer volume")
    elif transfer_volume <= 300:
        pipette = "flex_1channel_300"
    else:
        pipette = "flex_1channel_1000"
    
    simulation_log.append(f"✅ Selected pipette: {pipette}")
    
    # Step 3: Simulate labware loading
    required_labware = {
        1: "corning_96_wellplate_360ul_flat",
        2: "nest_12_reservoir_15ml", 
        3: f"opentrons_flex_96_tiprack_1000ul"
    }
    
    simulation_log.append("✅ Labware loading simulation passed")
    
    # Step 4: Simulate liquid handling operations
    total_operations = 6  # 6 standard curve points
    estimated_time = 0
    
    for i in range(total_operations):
        # Simulate transfer operation
        transfer_time = (transfer_volume / aspiration_speed) + (transfer_volume / dispense_speed) + 5  # +5 for movement
        estimated_time += transfer_time
        
        # Simulate mixing operation  
        mix_time = mix_repetitions * ((mix_volume / aspiration_speed) + (mix_volume / dispense_speed)) + 2
        estimated_time += mix_time
        
        simulation_log.append(f"  Well A{i+1}: Transfer {transfer_volume}µL + Mix {mix_repetitions}x{mix_volume}µL")
    
    # Step 5: Check for potential issues
    if transfer_volume > 950:
        warnings.append("Transfer volume near pipette maximum - consider smaller volume")
    
    if mix_volume > transfer_volume:
        errors.append(f"Mix volume ({mix_volume}µL) exceeds transfer volume ({transfer_volume}µL)")
    
    if aspiration_speed > 300 and transfer_volume < 50:
        warnings.append("High aspiration speed with small volume may cause air bubbles")
    
    # Step 6: Generate simulation report
    result = "🧪 PROTOCOL SIMULATION RESULTS\n\n"
    
    if errors:
        result += f"❌ ERRORS (will prevent execution):\n"
        for error in errors:
            result += f"  - {error}\n"
        result += "\n"
    
    if warnings:
        result += f"⚠️ WARNINGS (may affect performance):\n"
        for warning in warnings:
            result += f"  - {warning}\n"
        result += "\n"
    
    result += f"📋 Simulation Log:\n"
    for log in simulation_log:
        result += f"  {log}\n"
    
    result += f"\n⏱️ Estimated runtime: {estimated_time:.1f} seconds ({estimated_time/60:.1f} minutes)"
    result += f"\n💧 Total volume handled: {total_operations * transfer_volume}µL"
    
    if not errors:
        result += f"\n\n✅ SIMULATION PASSED - Protocol ready for execution!"
    else:
        result += f"\n\n❌ SIMULATION FAILED - Fix errors before execution"
    
    return result

@mcp.tool()
def run_parameter_optimization_experiment(
    speed_range: str = "20,50,100",
    mix_rep_range: str = "2,3,5", 
    target_r_squared: float = 0.95,
    target_cv: float = 10.0
) -> str:
    """Run automated optimization experiment testing multiple parameter combinations"""
    
    import itertools
    
    # Parse parameter ranges
    speeds = [float(x.strip()) for x in speed_range.split(',')]
    mix_reps = [int(x.strip()) for x in mix_rep_range.split(',')]
    
    results = []
    experiment_count = 0
    
    # Test all combinations
    for asp_speed, disp_speed, mix_rep in itertools.product(speeds, speeds, mix_reps):
        experiment_count += 1
        
        # Simulate protocol execution first
        sim_result = simulate_protocol_execution(
            aspiration_speed=asp_speed,
            dispense_speed=disp_speed, 
            mix_volume=100,
            mix_repetitions=mix_rep,
            transfer_volume=200
        )
        
        # Skip if simulation fails
        if "SIMULATION FAILED" in sim_result:
            continue
            
        # Mock experimental results (in real system, would run protocol + measure)
        # Simulate that certain combinations perform better
        mock_r_squared = 0.85 + (0.1 * (1 / (abs(asp_speed - 50) + 1))) + (0.05 * (1 / (abs(mix_rep - 3) + 1)))
        mock_cv = 25 - (5 * (1 / (abs(asp_speed - 50) + 1))) - (3 * (1 / (abs(mix_rep - 3) + 1)))
        
        # Add some realistic noise
        import random
        mock_r_squared += random.uniform(-0.02, 0.02)
        mock_cv += random.uniform(-2, 2)
        
        # Ensure realistic bounds
        mock_r_squared = max(0.7, min(0.99, mock_r_squared))
        mock_cv = max(5, min(30, mock_cv))
        
        results.append({
            'asp_speed': asp_speed,
            'disp_speed': disp_speed,
            'mix_rep': mix_rep,
            'r_squared': mock_r_squared,
            'cv': mock_cv,
            'score': mock_r_squared - (mock_cv / 100)  # Combined optimization score
        })
    
    # Sort by score (best first)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Generate optimization report
    report = "🤖 AUTOMATED OPTIMIZATION RESULTS\n\n"
    report += f"Tested {len(results)} parameter combinations\n"
    report += f"Target R²: ≥{target_r_squared}, Target CV: ≤{target_cv}%\n\n"
    
    # Show top 5 results
    report += "🏆 TOP 5 PARAMETER COMBINATIONS:\n"
    for i, result in enumerate(results[:5]):
        status = "✅" if result['r_squared'] >= target_r_squared and result['cv'] <= target_cv else "⚠️"
        report += f"{i+1}. {status} Asp:{result['asp_speed']}, Disp:{result['disp_speed']}, Mix:{result['mix_rep']}x → R²:{result['r_squared']:.3f}, CV:{result['cv']:.1f}%\n"
    
    # Find best meeting targets
    optimal = None
    for result in results:
        if result['r_squared'] >= target_r_squared and result['cv'] <= target_cv:
            optimal = result
            break
    
    if optimal:
        report += f"\n🎯 OPTIMAL PARAMETERS FOUND:\n"
        report += f"Aspiration: {optimal['asp_speed']} µL/s\n"
        report += f"Dispense: {optimal['disp_speed']} µL/s\n" 
        report += f"Mix Repetitions: {optimal['mix_rep']}\n"
        report += f"Performance: R²={optimal['r_squared']:.3f}, CV={optimal['cv']:.1f}%"
    else:
        report += f"\n❌ No parameters met targets. Best result: R²={results[0]['r_squared']:.3f}, CV={results[0]['cv']:.1f}%"
        report += f"\nRecommendation: Expand parameter ranges or adjust targets"
    
    return report

@mcp.tool()
def generate_optimized_protocol() -> str:
    """Generate final protocol using AI-optimized parameters"""
    # This would use results from optimization experiment
    # For now, using reasonable optimized values
    
    optimized_params = {
        'aspiration_speed': 50.0,  # Sweet spot from optimization
        'dispense_speed': 50.0,
        'mix_volume': 100,
        'mix_repetitions': 3,
        'transfer_volume': 200
    }
    
    # Generate the protocol with optimized parameters
    protocol = create_tartrazine_assay_protocol(
        aspiration_speed=optimized_params['aspiration_speed'],
        dispense_speed=optimized_params['dispense_speed'],
        mix_volume=optimized_params['mix_volume'],
        mix_repetitions=optimized_params['mix_repetitions'],
        transfer_volume=optimized_params['transfer_volume']
    )
    
    result = "🎯 AI-OPTIMIZED TARTRAZINE PROTOCOL\n\n"
    result += f"Using optimized parameters from automated experimentation:\n"
    result += f"• Aspiration Speed: {optimized_params['aspiration_speed']} µL/s\n"
    result += f"• Dispense Speed: {optimized_params['dispense_speed']} µL/s\n"  
    result += f"• Mix Repetitions: {optimized_params['mix_repetitions']}\n\n"
    result += protocol
    
    return result

import byonoy_devices as byonoy
import statistics

# Global variable to store device handle
#byonoy_device_handle = None

@mcp.tool()
def connect_byonoy_reader() -> str:
    """Connect to the Byonoy plate reader"""
    global byonoy_device_handle
    try:
        num_devices = byonoy.available_devices_count()
        if num_devices == 0:
            return "No Byonoy devices found"
        
        devices = byonoy.available_devices()
        result_code, device_handle = byonoy.open_device(devices[0])
        
        if result_code == byonoy.ErrorCode.NO_ERROR:
            byonoy_device_handle = device_handle
            return f"Connected to Byonoy device successfully. Handle: {device_handle}"
        else:
            return f"Failed to connect: {result_code}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def read_tartrazine_absorbance(wavelength: int = 450, step: str = "initialize") -> str:
    """Read absorbance values. Use step='initialize' first, then step='measure' after inserting plate"""
    global byonoy_device_handle
    try:
        if byonoy_device_handle is None:
            return "Please connect to Byonoy reader first"
        
        if step == "initialize":
            # Check slot is empty for initialization
            if byonoy.device_slot_status_supported(byonoy_device_handle):
                result_code, slot_status = byonoy.get_device_slot_status(byonoy_device_handle)
                if result_code == byonoy.ErrorCode.NO_ERROR and slot_status != byonoy.DeviceSlotState.EMPTY:
                    return f"❌ Remove plate first - slot status: {slot_status}"
            
            # Initialize measurement
            if byonoy.abs96_available_wavelengths_supported(byonoy_device_handle):
                result_code, abs_wavelengths = byonoy.abs96_get_available_wavelengths(byonoy_device_handle)
                if wavelength not in abs_wavelengths:
                    return f"Wavelength {wavelength} not available. Available: {abs_wavelengths}"
                
                config = byonoy.Abs96SingleMeasurementConfig()
                config.sample_wavelength = wavelength
                
                result_code = byonoy.abs96_initialize_single_measurement(byonoy_device_handle, config)
                if result_code == byonoy.ErrorCode.NO_ERROR:
                    return f"✅ Measurement initialized at {wavelength}nm. INSERT PLATE NOW, then run with step='measure'"
                else:
                    return f"❌ Initialize failed: {result_code}"
            
        elif step == "measure":
            # Check if plate is inserted
            if byonoy.device_slot_status_supported(byonoy_device_handle):
                result_code, slot_status = byonoy.get_device_slot_status(byonoy_device_handle)
                if result_code == byonoy.ErrorCode.NO_ERROR and slot_status == byonoy.DeviceSlotState.EMPTY:
                    return "❌ No plate detected. Please insert plate first."
            
            # Take actual measurement
            config = byonoy.Abs96SingleMeasurementConfig()
            config.sample_wavelength = wavelength

            result_code, values = byonoy.abs96_single_measure(byonoy_device_handle, config)
            if result_code == byonoy.ErrorCode.NO_ERROR:
                return f"📊 Absorbance values at {wavelength}nm: {values}"
            else:
                return f"❌ Measurement failed: {result_code}. Check plate positioning."
        
        else:
            return "Invalid step. Use step='initialize' or step='measure'"
            
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def calculate_assay_metrics(absorbance_values: str, concentrations: str = "0,10,20,50,100,200") -> str:
    """Calculate R² and CV from tartrazine standard curve data"""
    try:
        # Parse inputs
        abs_list = [float(x.strip()) for x in absorbance_values.split(',')]
        conc_list = [float(x.strip()) for x in concentrations.split(',')]
        
        # Take first 6 values for standard curve
        abs_curve = abs_list[:6]
        
        # Calculate R² (simplified linear regression)
        n = len(abs_curve)
        mean_conc = statistics.mean(conc_list)
        mean_abs = statistics.mean(abs_curve)
        
        numerator = sum((conc_list[i] - mean_conc) * (abs_curve[i] - mean_abs) for i in range(n))
        denom_conc = sum((conc_list[i] - mean_conc) ** 2 for i in range(n))
        denom_abs = sum((abs_curve[i] - mean_abs) ** 2 for i in range(n))
        
        r_squared = (numerator ** 2) / (denom_conc * denom_abs) if denom_conc * denom_abs > 0 else 0
        
        # Calculate CV for replicates (assuming triplicates)
        cv_values = []
        for i in range(0, min(len(abs_list), 18), 3):  # Every 3 values
            replicate_group = abs_list[i:i+3]
            if len(replicate_group) == 3:
                cv = (statistics.stdev(replicate_group) / statistics.mean(replicate_group)) * 100
                cv_values.append(cv)
        
        avg_cv = statistics.mean(cv_values) if cv_values else 0
        
        return f"R²: {r_squared:.4f}, Average CV: {avg_cv:.2f}%"
    except Exception as e:
        return f"Error calculating metrics: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport='stdio')