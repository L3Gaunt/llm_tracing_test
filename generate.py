import sys
from challenge_generator import generate_challenge

# Example usage
if __name__ == "__main__":
    # You can provide custom parameters or use defaults
    challenge, answer = generate_challenge(N=10, M=5, order='normal')
    
    # Print the challenge
    print(challenge)
    
    # Print the answer (to stderr for verification during testing)
    print(f'Correct value: {answer}', file=sys.stderr)
