import sys
import argparse
from challenge_generator import generate_challenge

# Example usage
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate variable reference challenges")
    parser.add_argument("--num-vars", type=int, default=10, help="Total number of variables in the challenge (default: 10)")
    parser.add_argument("--initializations-per-symbol", type=int, default=1, help="Number of times each symbol is directly initialized (default: 2)")
    parser.add_argument("--num-symbols", type=int, default=2, help="Number of distinct 3-digit symbols (default: 3)")
    parser.add_argument("--mode", type=str, default="normal", choices=["normal", "inverse", "random"], 
                      help="Order mode for the assignments (default: normal)")
    args = parser.parse_args()
    
    # Generate challenge with provided parameters
    sequence, last_var_value = generate_challenge(
        num_vars=args.num_vars,
        initializations_per_symbol=args.initializations_per_symbol,
        num_symbols=args.num_symbols,
        mode=args.mode
    )
    
    # Print the challenge
    for line in sequence:
        print(line)
    
    # Print the answer (to stderr for verification during testing)
    print(f'Correct value: {last_var_value}', file=sys.stderr)
