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

    symbols = random.sample(vocab, k=num_symbols)*initializations_per_symbol
    random.shuffle(symbols)

    sequence = []
    values = {}

    for i, var in enumerate(variables):
        if i % num_initializations == 0:
            random.shuffle(symbols)

        values[var] = symbols[i] if i < num_initializations else values[symbols[i % num_initializations]]
        sequence.append(f"{var} = {symbols[i % num_initializations]}")
        symbols[i % num_initializations] = var
        print(sequence[-1])
    
    last_var_value = values[variables[-1]]
    last_var = variables[-1]

    if mode == "inverse":
        sequence.reverse()
    if mode == "random":
        random.shuffle(sequence)

    return sequence, last_var_value, last_var


def generate_question(last_var):
    """
    Generate a question asking for the value of the last variable.
    
    Parameters:
    - last_var: The name of the last variable
    
    Returns:
    - question: A string containing the question
    """
    return f"Output only the result: What is the value of {last_var}?"


## Remaining code is for testing, here we resolve the value of a variable based on the
# sequence of assignments, so we have somewhat robust tracking

def resolve_value(sequence, var):
    """
    Helper to resolve a variable's initial value.
    
    Parameters:
    - sequence: List of assignment strings
    - var: Variable to resolve
    
    Returns:
    - resolved_value: The initial value the variable resolves to
    - steps: Number of steps taken to resolve the variable
    """
    assignments = {line.split(" = ")[0]: line.split(" = ")[1] for line in sequence}
    current = var
    steps = 0
    while not (current in vocab):
        steps += 1
        current = assignments[current]
    print(f"Resolved {var} to {current} in {steps} steps")
    return current, steps

def calculate_expected_steps(num_vars, initializations_per_symbol, num_symbols, mode="normal"):
    """
    Calculate the expected number of steps to resolve the last variable.
    This is determined based on the problem parameters.
    
    Parameters:
    - num_vars: Total number of variables
    - initializations_per_symbol: Number of times each symbol is directly initialized
    - num_symbols: Number of distinct symbols
    - mode: The mode of the challenge ("normal", "inverse", or "random")
    
    Returns:
    - expected_steps: Expected number of steps to resolve the last variable
    """    
    # Calculate the number of direct initializations
    num_initializations = num_symbols * initializations_per_symbol
    
    # For normal or inverse mode, we can calculate the expected steps
    # The last variable resolves to the initial value after traversing through the dependency chain
    # The depth is roughly: (num_vars / num_initializations) - 1
    depth = (num_vars + num_initializations - 1) // num_initializations
        
    return depth

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
        
        # Calculate expected steps based on problem parameters
        expected_steps = calculate_expected_steps(
            num_vars, 
            initializations_per_symbol, 
            num_symbols, 
            mode
        )
        if expected_steps is not None:
            print(f"Expected resolution steps: {expected_steps}")
            
        # Resolve the value and get actual steps
        resolved, actual_steps = resolve_value(sequence, last_var)
        print(f"Resolved {last_var} to {resolved} in {actual_steps} steps")
        
        # Verify the resolved value matches the expected value
        assert resolved == last_var_value, f"Value mismatch: got {resolved}, expected {last_var_value}"
        
        # Compare expected and actual steps 
        if expected_steps is not None:
            assert actual_steps == expected_steps, f"Steps mismatch: got {actual_steps}, expected {expected_steps}"
            print(f"✓ Resolution steps match: {actual_steps}")
        else:
            print(f"✓ No expected steps prediction for {mode} mode")

        # Verify symbol counts
        direct_assignments = []
        for line in sequence:
            parts = line.split(" = ")
            if parts[1] in vocab:
                direct_assignments.append(parts[1])
                
        counts = {s: direct_assignments.count(s) for s in set(direct_assignments)}
        for s in set(direct_assignments):
            assert counts[s] == initializations_per_symbol, f"Symbol {s} used {counts[s]} times, expected {initializations_per_symbol}"
        
        print("Test passed!")

if __name__ == "__main__":
    run_tests()