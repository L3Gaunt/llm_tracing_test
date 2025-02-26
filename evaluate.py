import os
import json
import time
import argparse
import concurrent.futures
from collections import defaultdict
import sys
import shutil
import threading
from openai import OpenAI
from dotenv import load_dotenv
from challenge_generator import generate_challenge

# Load environment variables from .env file
load_dotenv()

# Rate limiting variables
MAX_REQUESTS_PER_SECOND = 5
REQUEST_TIMESTAMPS = []

# Terminal colors (if supported)
try:
    TERM_COLORS_SUPPORTED = sys.stdout.isatty() and os.name != 'nt'
except:
    TERM_COLORS_SUPPORTED = False

# Color codes
GREEN = '\033[92m' if TERM_COLORS_SUPPORTED else ''
YELLOW = '\033[93m' if TERM_COLORS_SUPPORTED else ''
BLUE = '\033[94m' if TERM_COLORS_SUPPORTED else ''
RED = '\033[91m' if TERM_COLORS_SUPPORTED else ''
RESET = '\033[0m' if TERM_COLORS_SUPPORTED else ''

# Constants
API_TIMEOUT = 5.0  # Timeout for API calls in seconds
TASK_TIMEOUT = 10.0  # Overall timeout for tasks (should be > API_TIMEOUT)

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
    client = OpenAI(api_key=api_key, timeout=5.0)  # 5 second timeout
    
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
    
    except TimeoutError:
        return {"error": "API request timed out (exceeded 5 seconds)"}
    except Exception as e:
        return {"error": str(e)}

def run_single_evaluation(num_symbols, num_vars, initializations_per_symbol, mode, response_format="json_object", verbose=False, question_padding=""):
    """
    Run a single evaluation and return the result
    
    Args:
        num_symbols (int): Number of distinct 3-digit symbols
        num_vars (int): Total number of variables in the challenge
        initializations_per_symbol (int): Number of times each symbol is directly initialized
        mode (str): Mode for equation ordering (normal, inverse, random)
        response_format (str): Response format
        verbose (bool): Whether to print detailed output
        question_padding (str): Additional padding to add to the question
        
    Returns:
        dict: Result of the evaluation including parameters and correctness
    """
    # Generate a challenge
    sequence, correct_answer, last_var = generate_challenge(
        num_vars=num_vars,
        initializations_per_symbol=initializations_per_symbol,
        num_symbols=num_symbols,
        mode=mode
    )
    
    # Convert sequence to string and add the question
    from challenge_generator import generate_question
    challenge_text = "\n".join(sequence)
    question = generate_question(last_var)
    challenge = challenge_text + "\n\n" + question + question_padding
    
    if verbose:
        print(f"\nRunning evaluation with num_symbols={num_symbols}, num_vars={num_vars}, initializations_per_symbol={initializations_per_symbol}, mode={mode}")
    
    # Evaluate with OpenAI
    result = evaluate_with_openai(challenge, response_format=response_format)
    
    # Check if there was an error
    if "error" in result:
        error_message = result["error"]
        if verbose:
            print(f"API Error: {error_message}")
            print("Challenge:")
            print(challenge)
            print(f"Correct answer: {correct_answer}")
        return {
            "num_symbols": num_symbols,
            "num_vars": num_vars,
            "initializations_per_symbol": initializations_per_symbol,
            "mode": mode,
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
        print("Challenge:")
        print(challenge)
        print(f"Correct answer: {correct_answer}")
        print(f"OpenAI answer: {openai_answer}")
        print(f"Is correct: {is_correct}")
    
    # Return evaluation details
    return {
        "num_symbols": num_symbols,
        "num_vars": num_vars,
        "initializations_per_symbol": initializations_per_symbol,
        "mode": mode,
        "challenge": challenge,
        "correct_answer": correct_answer,
        "openai_answer": openai_answer,
        "is_correct": is_correct,
        "has_error": False,
        "error_message": None
    }

def run_multiple_evaluations(num_symbols, num_vars, initializations_per_symbol, question_padding, modes, num_per_mode=10, response_format="json_object", verbose=False):
    """
    Run multiple evaluations in parallel for different modes
    
    Args:
        num_symbols (int): Number of distinct 3-digit symbols
        num_vars (int): Total number of variables in the challenge
        initializations_per_symbol (int): Number of times each symbol is directly initialized
        question_padding (str): Additional padding to add to the question
        modes (list): List of modes to evaluate (normal, inverse, random)
        num_per_mode (int): Number of evaluations per mode
        response_format (str): Response format
        verbose (bool): Whether to print detailed output
        
    Returns:
        dict: Results of evaluations grouped by mode
    """
    # Prepare tasks
    tasks = []
    for mode in modes:
        for _ in range(num_per_mode):
            tasks.append((num_symbols, num_vars, initializations_per_symbol, mode, response_format, verbose, question_padding))
    
    # Run evaluations in parallel
    results = []
    total = len(tasks)
    
    # Progress tracking counters
    submitted = 0     # Tasks submitted to the executor
    completed = 0     # Tasks with answers returned and evaluated
    in_progress = 0   # Tasks currently running
    timeouts = 0      # Tasks that timed out
    errors = 0        # Tasks that had API errors
    
    print(f"Running {total} evaluations ({num_per_mode} each for {', '.join(modes)})...")
    
    # Track futures as they're submitted and completed
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_REQUESTS_PER_SECOND) as executor:
        # Create a dict to store futures and their start times
        futures = {}
        future_start_times = {}
        
        # Submit initial batch of tasks
        batch_size = min(MAX_REQUESTS_PER_SECOND, total)
        for i in range(batch_size):
            future = executor.submit(run_single_evaluation, *tasks[i])
            futures[future] = tasks[i]
            future_start_times[future] = time.time()
            submitted += 1
            in_progress += 1
            
            # Update progress display
            _update_progress_display(submitted, in_progress, completed, total, timeouts, errors)
        
        # Process results as they complete and submit new tasks
        while futures:
            # Check for timeouts
            current_time = time.time()
            timed_out_futures = []
            for future, start_time in future_start_times.items():
                if not future.done() and current_time - start_time > TASK_TIMEOUT:
                    # This task has timed out
                    future.cancel()
                    timed_out_futures.append(future)
            
            # Process timed out futures
            for future in timed_out_futures:
                if future in futures:
                    # Create a timeout result
                    num_symbols, num_vars, initializations_per_symbol, mode, _, verbose, _ = futures[future]
                    result = {
                        "num_symbols": num_symbols,
                        "num_vars": num_vars,
                        "initializations_per_symbol": initializations_per_symbol,
                        "mode": mode,
                        "challenge": "",
                        "correct_answer": None,
                        "openai_answer": None,
                        "is_correct": False,
                        "has_error": True,
                        "error_message": f"Task timed out after {TASK_TIMEOUT} seconds"
                    }
                    results.append(result)
                    
                    # Update counters
                    timeouts += 1
                    completed += 1
                    in_progress -= 1
                    
                    # Clean up
                    del futures[future]
                    del future_start_times[future]
                    
                    # Submit a new task if available
                    if submitted < total:
                        new_future = executor.submit(run_single_evaluation, *tasks[submitted])
                        futures[new_future] = tasks[submitted]
                        future_start_times[new_future] = time.time()
                        submitted += 1
                        in_progress += 1
                    
                    # Update progress display
                    _update_progress_display(submitted, in_progress, completed, total, timeouts, errors)
            
            # Wait for the next future to complete (with timeout to allow checking for task timeouts)
            done, _ = concurrent.futures.wait(
                futures, 
                return_when=concurrent.futures.FIRST_COMPLETED,
                timeout=0.1
            )
            
            if not done:
                continue  # No futures completed, continue checking for timeouts
            
            # Process completed futures
            for future in done:
                try:
                    # Get result (the answer has been returned and evaluated at this point)
                    result = future.result()
                    results.append(result)
                    completed += 1
                    in_progress -= 1
                    
                    # Track errors
                    if result.get("has_error", False):
                        errors += 1
                        
                except Exception as e:
                    # Handle unexpected exceptions in the task
                    print(f"\nTask failed with unexpected exception: {e}")
                    num_symbols, num_vars, initializations_per_symbol, mode, _, verbose, _ = futures[future]
                    result = {
                        "num_symbols": num_symbols,
                        "num_vars": num_vars,
                        "initializations_per_symbol": initializations_per_symbol,
                        "mode": mode,
                        "challenge": "",
                        "correct_answer": None,
                        "openai_answer": None,
                        "is_correct": False,
                        "has_error": True,
                        "error_message": f"Unexpected error: {str(e)}"
                    }
                    results.append(result)
                    errors += 1
                    completed += 1
                    in_progress -= 1
                
                # Clean up
                if future in future_start_times:
                    del future_start_times[future]
                del futures[future]
                
                # Submit a new task if available
                if submitted < total:
                    new_future = executor.submit(run_single_evaluation, *tasks[submitted])
                    futures[new_future] = tasks[submitted]
                    future_start_times[new_future] = time.time()
                    submitted += 1
                    in_progress += 1
                
                # Update progress display
                _update_progress_display(submitted, in_progress, completed, total, timeouts, errors)
    
    # Print final summary
    print("\nAll evaluations completed!")
    if timeouts > 0 or errors > 0:
        print(f"{RED}Issues:{RESET} {timeouts} timeouts, {errors} API errors")
    
    return results

def _update_progress_display(submitted, in_progress, completed, total, timeouts, errors):
    """
    Update the progress display with current status
    
    Args:
        submitted (int): Number of tasks submitted/started
        in_progress (int): Number of tasks currently in progress
        completed (int): Number of tasks completed (answers returned and evaluated)
        total (int): Total number of tasks
        timeouts (int): Number of tasks that timed out
        errors (int): Number of tasks with API errors
    """
    # Get terminal width for dynamic sizing
    try:
        term_width = shutil.get_terminal_size().columns
    except:
        term_width = 80  # Default width
    
    # Calculate progress percentage
    percentage = (completed / total) * 100 if total > 0 else 0
    
    # Create progress bar (scales with terminal width)
    bar_length = min(20, max(10, term_width // 8))
    filled_length = int(bar_length * completed // total) if total > 0 else 0
    progress_bar = f"[{GREEN}{'=' * filled_length}{RESET}{' ' * (bar_length - filled_length)}]"
    
    # Calculate successful completions
    successful = completed - timeouts - errors
    
    # Create status line
    status_line = (
        f"Progress: {progress_bar} {BLUE}{percentage:.1f}%{RESET} | "
        f"Submitted: {YELLOW}{submitted}/{total}{RESET} | "
        f"Running: {YELLOW}{in_progress}{RESET} | "
        f"Evaluated: {GREEN}{successful}{RESET}"
    )
    
    # Add error information if any
    if timeouts > 0 or errors > 0:
        status_line += f" | {RED}Timeouts: {timeouts}, Errors: {errors}{RESET}"
    
    # Ensure the status line fits in the terminal
    if len(status_line) - (len(GREEN) + len(BLUE) + len(YELLOW) + len(RED) + len(RESET) * 5) > term_width:
        # Simplified version without colors for narrow terminals
        status_line = f"Progress: {percentage:.1f}% | Running: {in_progress} | Success: {successful} | Issues: {timeouts+errors}"
    
    # Clear the line and print status
    print("\r" + " " * (term_width - 1) + "\r" + status_line, end="")

def calculate_success_rates(results):
    """
    Calculate success rates from evaluation results
    
    Args:
        results (list): List of evaluation results
        
    Returns:
        dict: Success rates by mode
    """
    # Group results by mode
    grouped_results = defaultdict(list)
    for result in results:
        key = f"{result['mode']}"
        grouped_results[key].append(result)
    
    # Calculate success rates and error rates
    success_rates = {}
    for key, key_results in grouped_results.items():
        total = len(key_results)
        successful = sum(1 for r in key_results if r["is_correct"])
        errors = sum(1 for r in key_results if r.get("has_error", False))
        incorrect = total - successful - errors
        
        success_rates[key] = {
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
    parser.add_argument("--num-symbols", type=int, default=5, 
                        help="Number of distinct 3-digit symbols (default: 5)")
    parser.add_argument("--num-vars", type=int, default=50, 
                        help="Total number of variables in the challenge (default: 50)")
    parser.add_argument("--initializations-per-symbol", type=int, default=7, 
                        help="Number of times each symbol is directly initialized (default: 7)")
    parser.add_argument("--question-padding", type=str, default="", 
                        help="Padding for the question (default: empty string)")
    parser.add_argument("--num-per-mode", type=int, default=10, 
                        help="Number of evaluations per mode (default: 10)")
    parser.add_argument("--format", type=str, default="json_object", choices=["json_object", "text"], 
                        help="Response format from OpenAI (default: json_object)")
    parser.add_argument("--verbose", action="store_true", 
                        help="Print detailed output for each evaluation (default: False)")
    args = parser.parse_args()
    
    # Modes to evaluate
    modes = ["normal", "inverse", "random"]
    
    # Run evaluations
    results = run_multiple_evaluations(
        num_symbols=args.num_symbols,
        num_vars=args.num_vars,
        initializations_per_symbol=args.initializations_per_symbol,
        question_padding=args.question_padding,
        modes=modes,
        num_per_mode=args.num_per_mode,
        response_format=args.format,
        verbose=args.verbose
    )
    
    # Calculate success rates
    success_rates = calculate_success_rates(results)
    
    # Print results
    print("\n===== EVALUATION RESULTS =====")
    print(f"Parameters: num_symbols={args.num_symbols}, num_vars={args.num_vars}, initializations_per_symbol={args.initializations_per_symbol}, {args.num_per_mode} evaluations per mode")
    print("\nSuccess Rates:")
    
    for key, stats in success_rates.items():
        if key != "overall":
            print(f"  {key}: {stats['successful']}/{stats['total']} " 
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
            print(f"Mode: {error['mode']}, num_symbols={error['num_symbols']}, "
                  f"num_vars={error['num_vars']}, "
                  f"initializations_per_symbol={error['initializations_per_symbol']}")

if __name__ == "__main__":
    main() 