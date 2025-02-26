import random
import string

def generate_challenge(N=5, M=5, trackback_depth=0, seed=None, order='normal'):
    """
    Generates a variable reference challenge with N levels and M variables per level.
    
    Args:
        N (int): Number of levels (0 to N-1)
        M (int): Number of variables per level
        trackback_depth (int): How many levels back a variable can reference. 
                               0 means only previous level, 1 means up to 2 levels back, etc.
        seed (int, optional): Random seed for reproducibility
        order (str): Order of equations in output: 'normal', 'randomized', or 'reversed'
        
    Returns:
        tuple: (challenge_text, correct_answer)
    """
    # Set seed if provided
    if seed is not None:
        random.seed(seed)
        
    # Generate a pool of possible random IDs (ensuring we have enough)
    max_id = 1000  # Upper limit for variable IDs
    total_vars = N * M
    random_ids = random.sample(range(1, max_id + 1), total_vars)
    
    # Generate variable names with randomized IDs: V42, V317, etc.
    variables = [f'V{random_ids[i]}' for i in range(total_vars)]

    # Group variables into levels
    # Level 0: first M variables, Level 1: next M variables, etc.
    levels = [variables[k * M:(k + 1) * M] for k in range(N)]

    # Initialize a dictionary to store assignments
    assignments = {}

    # Assign random letters to level 0 variables
    for var in levels[0]:
        assignments[var] = random.choice(string.ascii_uppercase)

    # Assign references for variables in higher levels
    # Each variable in level k references a variable from a range of previous levels
    for k in range(1, N):
        for var in levels[k]:
            # Calculate the lower bound level
            lower_bound = max(0, k - trackback_depth - 1)
            
            # Collect all variables from level lower_bound to level k-1
            available_vars = []
            for level_idx in range(lower_bound, k):
                available_vars.extend(levels[level_idx])
            
            # Randomly choose a variable from the available levels
            ref_var = random.choice(available_vars)
            assignments[var] = ref_var

    # Select a variable from the last level to query
    query_var = random.choice(levels[-1])

    # Build the challenge text
    challenge_lines = []
    
    # Create all equation lines first
    equation_lines = []
    for level in levels:
        for var in level:
            if isinstance(assignments[var], str) and len(assignments[var]) == 1 and assignments[var] in string.ascii_uppercase:
                # Level 0 variables are letters
                equation_lines.append(f'{var} = {assignments[var]}')
            else:
                # Higher-level variables reference other variables
                equation_lines.append(f'{var} = {assignments[var]}')
    
    # Apply the requested order
    if order == 'normal':
        # Keep the equations in level order (default behavior)
        pass
    elif order == 'randomized':
        # Shuffle the equations
        random.shuffle(equation_lines)
    elif order == 'reversed':
        # Reverse the order of equations (last level first)
        equation_lines.reverse()
    else:
        raise ValueError("Order must be one of: 'normal', 'randomized', 'reversed'")
    
    # Add equation lines to challenge
    challenge_lines.extend(equation_lines)

    # Pose the question
    challenge_lines.append(f'What is the value of {query_var}? Start your answer with the result and then explain it.')
    
    challenge_text = '\n'.join(challenge_lines)
    
    # Compute the correct value
    def resolve(var):
        if isinstance(assignments[var], str) and len(assignments[var]) == 1 and assignments[var] in string.ascii_uppercase:
            return assignments[var]
        else:
            return resolve(assignments[var])

    correct_value = resolve(query_var)
    
    return challenge_text, correct_value 