def test_substitution(properties):
    import numpy as np
    from pymatgen.core.periodic_table import Element
    
    expected_properties = {
        "site_specie_symbol": {
            "format": "str",
            "value": "N"
        },
        "substitution_symmetry_equivalence": {
            "format": "bool",
            "value": True
        },
        "substitution_string_representation": {
            "format": "str",
            "value": "O subsitituted on the N site at at site #3"
        },
        "substitution_oxidation_state": {
            "format": "int",
            "value": 1
        },
        "substitution_charge_states": {
            "format": "list",
            "value": [-1, 0, 1, 2]
        },
        "substitution_multiplicity": {
            "format": "int",
            "value": 2
        },
        "supercell_site_specie_symbol": {
            "format": "str",
            "value": "O"
        },
        "supercell_formula": {
            "format": "str",
            "value": "Ga64 N63 O1"
        },
        "substitution_name": {
            "format": "str",
            "value": "O_N"
        },
        "substitution_latex_name": {
            "format": "str",
            "value": "O$_{\\rm N}$"
        },
        "substitution_element_changes": {
            "format": "dict",
            "value": {Element('N'): -1, Element('O'): 1}
        },
        "free_sites_intersection_ratio": {
            "format": "float",
            "value": 1.0
        },
        "perturbation_free_sites": {
            "format": "bool",
            "value": True
        },
        "user_defined_charge_states": {
            "format": "list",
            "value": [-100, 102]
        },
        "default_charge_states": {
            "format": "list",
            "value": [-1, 0, 1, 2]
        },
        "target_fractional_coordinates": {
            "format": "np.allclose",
            "value": [0.1250, 0.0833335, 0.18794]
        },
        "closest_equivalent_site_coordinates": {
            "format": "np.allclose",
            "value": [0.375, 0.5833335, 0.68794]
        },
        "antisite_charge_states": {
            "format": "list",
            "value": [-7, -6, -5, -4, -3, -2, -1, 0, 1]
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
        
        # Check type for np.allclose requirements
        if expected_format == "np.allclose":
            if not isinstance(actual_value, (list, np.ndarray)):
                errors.append(f"{property_name} is not of type list or np.ndarray")
                continue
            
            # Check value using np.allclose for approximate comparisons
            if not np.allclose(actual_value, expected_value):
                errors.append(f"{property_name}: Expected value close to {expected_value} but got {actual_value}")
        else:
            # Check type for other formats
            if not isinstance(actual_value, eval(expected_format)):
                errors.append(f"{property_name} is not of type {expected_format}")
                continue
            
            # Check value
            if actual_value != expected_value:
                errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
    
    if errors:
        errors.append(len(errors))
        errors.append(len(expected_properties))
        return errors
    else:
        return "ok"