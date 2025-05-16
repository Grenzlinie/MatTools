def test_closest_sc_mat(properties):
    import numpy as np
    expected_properties = {
        "supercell_structure_matching": {
            "format": "bool",
            "value": True
        },
        "closest_supercell_matrix": {
            "format": "np.allclose",
            "value": np.array([[2, 1, 2], [2, 0, 3], [2, 1, 1]])
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
        
        # Check type before numerical comparison
        if expected_format == "np.allclose":
            if not isinstance(actual_value, (list, np.ndarray)):
                errors.append(f"{property_name} is not of type list or np.ndarray")
                continue
            if not np.allclose(actual_value, expected_value):
                errors.append(f"{property_name}: Expected value close to {expected_value} but got {actual_value}")
        else:
            if not isinstance(actual_value, eval(expected_format)):
                errors.append(f"{property_name} is not of type {expected_format}")
                continue
            if actual_value != expected_value:
                errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
    
    if errors:
        errors.append(len(errors))
        errors.append(len(expected_properties))
        return errors
    else:
        return "ok"