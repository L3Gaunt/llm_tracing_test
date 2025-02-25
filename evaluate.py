import os
import json
import time
import argparse
import concurrent.futures
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv
from challenge_generator import generate_challenge

# Load environment variables from .env file
load_dotenv()

# Rate limiting variables
MAX_REQUESTS_PER_SECOND = 10
REQUEST_TIMESTAMPS = []

def rate_limit():
    """
    Implements a rate limiter to prevent exceeding MAX_REQUESTS_PER_SECOND
    """
    global REQUEST_TIMESTAMPS
    
    current_time = time.time()
    # Keep only timestamps from the last second
    REQUEST_TIMESTAMPS = [ts for ts in REQUEST_TIMESTAMPS if current_time - ts < 1.0]
    
    # If we've hit the limit, wait until we can make another request
    if len(REQUEST_TIMESTAMPS) >= MAX_REQUESTS_PER_SECOND:
        sleep_time = 1.0 - (current_time - REQUEST_TIMESTAMPS[0])
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    # Add current timestamp to the list
    REQUEST_TIMESTAMPS.append(time.time())

def evaluate_with_openai(challenge, response_format="json_object"):
    """
    Evaluate a challenge using OpenAI API with GPT-4o-mini in JSON mode
    
    Args:
        challenge (str): The challenge to evaluate
        response_format (str): The response format (json_object or text)
        
    Returns:
        dict: The response from OpenAI
    """
    # Apply rate limiting
    rate_limit()
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Define the system message and user prompt
    system_message = {
        "role": "system",
        "content": "You are a helpful assistant that solves variable reference challenges. Please provide your answer as a JSON object with a single field 'answer' containing the result (which could be a number, letter, or other value)."
    }
    
    user_message = {
        "role": "user",
        "content": f"Solve this variable reference challenge and provide only the final answer:\n\n{challenge}"
    }
    
    # Set response format for JSON mode
    format_param = {"type": response_format}
    
    # Make the API call
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[system_message, user_message],
            response_format=format_param
        )
        
        # Extract and parse the response
        if response_format == "json_object":
            result = json.loads(response.choices[0].message.content)
            return result
        else:
            return {"raw_response": response.choices[0].message.content}
    
    except Exception as e:
        return {"error": str(e)}

def run_single_evaluation(n, m, order, response_format="json_object", verbose=False, whitespace_padding=12000):
    """
    Run a single evaluation and return the result
    
    Args:
        n (int): Number of levels
        m (int): Number of variables per level
        order (str): Order of equations
        response_format (str): Response format
        verbose (bool): Whether to print detailed output
        
    Returns:
        dict: Result of the evaluation including parameters and correctness
    """
    # Generate a challenge
    challenge, correct_answer = generate_challenge(N=n, M=m, order=order)
    
    challenge += " "*whitespace_padding
    if verbose:
        print(f"\nRunning evaluation with N={n}, M={m}, order={order}")
        print("Challenge:")
        print(challenge)
        print("Correct answer:", correct_answer)
    
    # Evaluate with OpenAI
    result = evaluate_with_openai(challenge, response_format=response_format)
    
    # Check if there was an error
    if "error" in result:
        error_message = result["error"]
        if verbose:
            print(f"API Error: {error_message}")
        return {
            "n": n,
            "m": m,
            "order": order,
            "challenge": challenge,
            "correct_answer": correct_answer,
            "openai_answer": None,
            "is_correct": False,
            "has_error": True,
            "error_message": error_message
        }
    
    # Check if the answer is correct
    is_correct = False
    openai_answer = None
    
    if "answer" in result:
        openai_answer = result["answer"]
        # Compare as strings to handle both numerical and non-numerical answers
        openai_answer_str = str(openai_answer).strip()
        correct_answer_str = str(correct_answer).strip()
        is_correct = openai_answer_str == correct_answer_str
    
    if verbose:
        print(f"OpenAI answer: {openai_answer}")
        print(f"Correct answer: {correct_answer}")
        print(f"Is correct: {is_correct}")
    
    # Return evaluation details
    return {
        "n": n,
        "m": m,
        "order": order,
        "challenge": challenge,
        "correct_answer": correct_answer,
        "openai_answer": openai_answer,
        "is_correct": is_correct,
        "has_error": False,
        "error_message": None
    }

def run_multiple_evaluations(n, m, orders, num_per_order=10, response_format="json_object", verbose=False):
    """
    Run multiple evaluations in parallel for different order modes
    
    Args:
        n (int): Number of levels
        m (int): Number of variables per level
        orders (list): List of order modes to evaluate
        num_per_order (int): Number of evaluations per order mode
        response_format (str): Response format
        verbose (bool): Whether to print detailed output
        
    Returns:
        dict: Results of evaluations grouped by order mode
    """
    # Prepare tasks
    tasks = []
    for order in orders:
        for _ in range(num_per_order):
            tasks.append((n, m, order, response_format, verbose))
    
    # Run evaluations in parallel
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_REQUESTS_PER_SECOND) as executor:
        future_to_task = {executor.submit(run_single_evaluation, *task): task for task in tasks}
        completed = 0
        total = len(tasks)
        
        print(f"Running {total} evaluations ({num_per_order} each for {', '.join(orders)})...")
        
        for future in concurrent.futures.as_completed(future_to_task):
            completed += 1
            print(f"Progress: {completed}/{total} evaluations completed", end="\r")
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Evaluation failed: {e}")
        
        print("\nAll evaluations completed!")
    
    return results

def calculate_success_rates(results):
    """
    Calculate success rates from evaluation results
    
    Args:
        results (list): List of evaluation results
        
    Returns:
        dict: Success rates by order mode
    """
    # Group results by order
    grouped_results = defaultdict(list)
    for result in results:
        grouped_results[result["order"]].append(result)
    
    # Calculate success rates and error rates
    success_rates = {}
    for order, order_results in grouped_results.items():
        total = len(order_results)
        successful = sum(1 for r in order_results if r["is_correct"])
        errors = sum(1 for r in order_results if r.get("has_error", False))
        incorrect = total - successful - errors
        
        success_rates[order] = {
            "total": total,
            "successful": successful,
            "errors": errors,
            "incorrect": incorrect,
            "success_rate": successful / total if total > 0 else 0,
            "error_rate": errors / total if total > 0 else 0
        }
    
    # Calculate overall success rate
    total_all = len(results)
    successful_all = sum(1 for r in results if r["is_correct"])
    errors_all = sum(1 for r in results if r.get("has_error", False))
    incorrect_all = total_all - successful_all - errors_all
    
    success_rates["overall"] = {
        "total": total_all,
        "successful": successful_all,
        "errors": errors_all,
        "incorrect": incorrect_all,
        "success_rate": successful_all / total_all if total_all > 0 else 0,
        "error_rate": errors_all / total_all if total_all > 0 else 0
    }
    
    return success_rates

def main():
    parser = argparse.ArgumentParser(description="Evaluate variable reference challenges using OpenAI API")
    parser.add_argument("--n", type=int, default=50, help="Number of levels")
    parser.add_argument("--m", type=int, default=2, help="Number of variables per level")
    parser.add_argument("--num-per-order", type=int, default=100, help="Number of evaluations per order type")
    parser.add_argument("--format", type=str, default="json_object", choices=["json_object", "text"], 
                        help="Response format from OpenAI")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output for each evaluation")
    args = parser.parse_args()
    
    # Orders to evaluate
    orders = ["normal", "reversed", "randomized"]
    
    # Run evaluations
    results = run_multiple_evaluations(
        n=args.n,
        m=args.m,
        orders=orders,
        num_per_order=args.num_per_order,
        response_format=args.format,
        verbose=args.verbose
    )
    
    # Calculate success rates
    success_rates = calculate_success_rates(results)
    
    # Print results
    print("\n===== EVALUATION RESULTS =====")
    print(f"Parameters: N={args.n}, M={args.m}, {args.num_per_order} evaluations per order type")
    print("\nSuccess Rates:")
    
    for order, stats in success_rates.items():
        if order != "overall":
            print(f"  {order.capitalize()}: {stats['successful']}/{stats['total']} " 
                  f"({stats['success_rate']*100:.1f}%) | "
                  f"Errors: {stats['errors']} ({stats['error_rate']*100:.1f}%) | "
                  f"Incorrect: {stats['incorrect']} ({(1-stats['success_rate']-stats['error_rate'])*100:.1f}%)")
    
    # Print overall success rate
    overall = success_rates["overall"]
    print(f"\nOverall: {overall['successful']}/{overall['total']} "
          f"({overall['success_rate']*100:.1f}%) | "
          f"Errors: {overall['errors']} ({overall['error_rate']*100:.1f}%) | "
          f"Incorrect: {overall['incorrect']} ({(1-overall['success_rate']-overall['error_rate'])*100:.1f}%)")
    
    # Print error examples if there were any errors
    error_examples = [r for r in results if r.get("has_error", False)]
    if error_examples and len(error_examples) > 0:
        print("\nError Examples:")
        # Show up to 3 examples
        for i, error in enumerate(error_examples[:3]):
            print(f"\nError {i+1}: {error['error_message']}")
            print(f"Order: {error['order']}, N={error['n']}, M={error['m']}")

if __name__ == "__main__":
    main() 