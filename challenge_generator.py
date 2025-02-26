import random

    # Generate variable names
    # experimental: vocab instead of symbols
vocab = [
    "Lantern", "Breeze", "Marble", "Quantum", "Cactus", "Whisper", "Falcon", 
    "Jigsaw", "Velvet", "Orbit", "Echo", "Glacier", "Sprocket", "Nimbus", 
    "Tundra", "Latch", "Zephyr", "Fable", "Alloy", "Harbor", "Riddle", 
    "Monsoon", "Pylon", "Serpent", "Chisel", "Vortex", "Waffle", "Ponder", 
    "Thistle", "Lush"
]

def generate_challenge(num_vars, initializations_per_symbol, num_symbols, seed=None, mode="normal"):
    """
    Generate a variable resolution challenge where each symbol is initialized exactly
    initializations_per_symbol times.

    Parameters:
    - num_vars: Total number of variables (e.g., V_001, V_002, ...)
    - initializations_per_symbol: Number of times each symbol is directly initialized
    - num_symbols: Number of distinct 3-digit symbols (e.g., 100, 101, ...)
    - seed (optional): Random seed for reproducibility
    - mode (default "normal", can be "normal", "inverse", "random"): Order in which relationships are outputted

    Returns:
    - sequence: List of assignment strings (e.g., "V001 = 100", "V002 = V001")
    - last_var_value: The initial symbol that the last variable resolves to
    - last_var: The name of the last variable in the sequence
    """
    if seed is not None:
        random.seed(seed)

    # Calculate total direct initializations
    num_initializations = num_symbols * initializations_per_symbol
    if num_initializations > num_vars:
        raise ValueError("Not enough variables to satisfy initializations per symbol")

    assert num_vars <= 900, "Number of variables must be less than or equal to 900"


    variables = [f"V_{i:03d}" for i in random.sample(range(100, 1000), k=num_vars)]

    assert num_symbols <= len(vocab)
    # Generate symbols (e.g., '100', '101', ...)
    symbols = random.sample(vocab, k=num_symbols)

    # Create values list with each symbol appearing exactly initializations_per_symbol times
    values_list = [symbol for symbol in symbols for _ in range(initializations_per_symbol)]
    
    
    random.shuffle(values_list)

    # Split variables into directly initialized and remaining
    directly_defined = variables[:num_initializations]
    remaining = variables[num_initializations:]

    # Track variables available for referencing
    currently_unreferenced_vars = list(directly_defined)

    # Initialize sequence and value tracking
    sequence = []
    var_values = {}  # Maps each variable to its resolved symbol

    # Assign direct initializations
    for var, value in zip(directly_defined, values_list):
        sequence.append(f"{var} = {value}")
        var_values[var] = value

    sequence_afterwards = []
    # Define remaining variables
    for var in remaining:
        chosen_var_index = random.randint(0, len(currently_unreferenced_vars) - 1)
        sequence_afterwards.append(f"{var} = {currently_unreferenced_vars[chosen_var_index]}")
        var_values[var] = var_values[currently_unreferenced_vars[chosen_var_index]]  # Inherit resolved value

        currently_unreferenced_vars[chosen_var_index] = var

    sequence = starter_sequence + sequence_afterwards[:-1]
    if mode == "inverse":
        sequence.reverse()
    if mode == "random":
        random.shuffle(sequence)
    
    sequence.append(sequence_afterwards[-1])

    # Store the last variable's value and name before any reordering
    last_var = remaining[-1]
    last_var_value = var_values[last_var]  

    return sequence, last_var_value, last_var


def generate_question(last_var):
    """
    Generate a question asking for the value of the last variable.
    
    Parameters:
    - last_var: The name of the last variable
    
    Returns:
    - question: A string containing the question
    """
    return f"What is the value of {last_var}? Output only the result."


## Remaining code is for testing, here we resolve the value of a variable based on the
# sequence of assignments, so we have somewhat robust tracking

def resolve_value(sequence, var):
    """Helper to resolve a variable's initial value."""
    assignments = {line.split(" = ")[0]: line.split(" = ")[1] for line in sequence}
    current = var
    counter = 0
    while not (assignments[current] in vocab):
        counter += 1
        current = assignments[current]
    print(f"Resolved {var} to {current} in {counter} steps")
    return assignments[current]

def run_tests():
    test_cases = [
        # Basic test cases
        (5, 1, 3),  # 3 initializations
        (10, 2, 3), # 6 initializations
        (25+2*3, 2, 3),  # 12 initializations
        # Test cases with different modes
        (50, 2, 3, 42, "normal"),  # With normal mode
        (50, 2, 3, 43, "inverse"),  # With inverse mode
        (50, 2, 3, 44, "random"),   # With random mode
    ]
    
    for test_case in test_cases:
        if len(test_case) == 3:
            num_vars, initializations_per_symbol, num_symbols = test_case
            seed = None
            mode = "normal"
        else:
            num_vars, initializations_per_symbol, num_symbols, seed, mode = test_case
            
        print(f"\nTest: {num_vars} vars, {initializations_per_symbol} per symbol, {num_symbols} symbols")
        print(f"Mode: {mode}, Seed: {seed}")
        
        sequence, last_var_value, last_var = generate_challenge(
            num_vars, 
            initializations_per_symbol, 
            num_symbols,
            seed=seed,
            mode=mode
        )
        
        for line in sequence:
            print(f"  {line}")
        
        question = generate_question(last_var)
        print(f"\nQuestion: {question}")
        print(f"Answer: {last_var_value}")
            
        resolved = resolve_value(sequence, last_var)
        print(f"Resolved {last_var} to {resolved}")
        assert resolved == last_var_value, "Value mismatch"

        # Verify symbol counts
        direct = [line.split(" = ")[1] for line in sequence if line.split(" = ")[1].isdigit()]
        counts = {s: direct.count(s) for s in direct}
        for s in set(direct):
            assert counts[s] == initializations_per_symbol, f"Symbol {s} used {counts[s]} times, expected {initializations_per_symbol}"
        print("Test passed!")

if __name__ == "__main__":
    run_tests()