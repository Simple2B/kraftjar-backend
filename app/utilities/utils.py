def pop_keys(dictionary: dict, keys: list[str]) -> dict:
    """Remove a list of keys from a dictionary. Returns the dictionary."""
    for key in keys:
        dictionary.pop(key, None)
    return dictionary
