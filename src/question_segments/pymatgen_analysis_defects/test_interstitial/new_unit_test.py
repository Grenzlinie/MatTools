def test_interstitial(properties):
    import numpy as np
    expected_properties = {
        "oxidation_state": {
            "format": "int",
            "value": 3
        },
        "charge_states": {
            "format": "list",
            "value": [-1, 0, 1, 2, 3, 4]
        },
        "fractional_coordinates": {
            "format": "np.allclose",
            "value": [0, 0, 0.75]
        },
        "supercell_formula": {
            "format": "str",
            "value": "Ga64 N65"
        },
        "defect_name": {
            "format": "str",
            "value": "N_i"
        },
        "defect_string_representation": {
            "format": "str",
            "value": "N intersitial site at [0.00,0.00,0.75]"
        },
        "element_changes": {
            "format": "dict",
            "value": {"N": 1}
        },
        "latex_name": {
            "format": "str",
            "value": "N$_{\\rm i}$"
        },
        "defect_fpos_initial": {
            "format": "np.allclose",
            "value": [0, 0, 0.398096581]
        },
        "defect_fpos_modified": {
            "format": "np.allclose",
            "value": [0.25, 0.5, 0.89809658]
        },
        "user_defined_charge_states": {
            "format": "list",
            "value": [-100, 102]
        }
    }
    
    errors = []
    
    for property_name, expected_info in expected_properties.items():
        expected_value = expected_info['value']
        expected_format = expected_info['format']
        
        if property_name not in properties:
            errors.append(f"{property_name} not found in input properties")
            continue
        
        actual_value = properties[property_name]
        
        # Check type for np.allclose cases
        if expected_format == "np.allclose":
            if not isinstance(actual_value, (np.ndarray, list)):
                errors.append(f"{property_name}: Actual value must be an array-like type for np.allclose")
                continue
        
        # Check type (skip type check for np.allclose cases as it's handled separately)
        if expected_format != "np.allclose" and not isinstance(actual_value, eval(expected_format)):
            errors.append(f"{property_name} is not of type {expected_format}")
            continue
        
        # Check value or use np.allclose for approximate comparisons
        if expected_format == "np.allclose":
            if not np.allclose(actual_value, expected_value):
                errors.append(f"{property_name}: Expected value close to {expected_value} but got {actual_value}")
        else:
            if actual_value != expected_value:
                errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
    
    if errors:
        errors.append(len(errors))
        errors.append(len(expected_properties))
        return errors
    else:
        return "ok"