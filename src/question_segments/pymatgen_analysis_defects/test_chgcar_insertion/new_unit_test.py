def test_chgcar_insertion(properties):
    import numpy as np
    expected_properties = {
        "average_charge": {
            "format": "np.allclose",
            "value": [0.03692438178614583, 0.10068764899215804]
        },
        "insertion_site_positions": {
            "format": "np.allclose",
            "value": [[[0.0, 0.0, 0.0], [0.0, 0.0, 0.5], [0.0, 0.5, 0.0], [0.5, 0.0, 0.0]], [[0.375, 0.375, 0.375], [0.625, 0.625, 0.625]]]
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
            if property_name == "insertion_site_positions":
                if not isinstance(actual_value, (list, np.ndarray)):
                    errors.append(f"{property_name} is not of type list or np.ndarray")
                    continue
                for actual, expected in zip(actual_value, expected_value):
                    if not np.allclose(actual, expected):
                        errors.append(f"{property_name}: Expected value close to {expected} but got {actual}")
            else:
                if not isinstance(actual_value, (float, np.float64, list, np.ndarray)):
                    errors.append(f"{property_name} is not of type float or list/np.ndarray")
                    continue
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