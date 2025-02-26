import sys
import argparse
from challenge_generator import generate_challenge

# Example usage
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate variable reference challenges")
    parser.add_argument("--n", type=int, default=10, help="Number of levels (default: 10)")
    parser.add_argument("--m", type=int, default=5, help="Number of variables per level (default: 5)")
    parser.add_argument("--trackback-depth", type=int, default=0, 
                        help="How many levels back variables can reference (0=previous level only, default: 0)")
    parser.add_argument("--order", type=str, default="normal", choices=["normal", "randomized", "reversed"],
                        help="Order of equations in output (default: normal)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    args = parser.parse_args()
    
    # Generate challenge with provided parameters
    challenge, answer = generate_challenge(
        N=args.n, 
        M=args.m, 
        trackback_depth=args.trackback_depth,
        seed=args.seed,
        order=args.order
    )
    
    # Print the challenge
    print(challenge)
    
    # Print the answer (to stderr for verification during testing)
    print(f'Correct value: {answer}', file=sys.stderr)
