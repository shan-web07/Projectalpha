import subprocess
import sys
import re


def compile_cpp(filename, executable_name):
    print(f"Compiling {filename}...")
    # Compiles with -O2/-std matching Codeforces' typical GNU G++ settings
    result = subprocess.run(
        ["g++", "-O2", "-std=c++17", filename, "-o", executable_name],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ Compilation Error in {filename}:\n{result.stderr}")
        sys.exit(1)


def get_time_limit_seconds(default=2.0):
    """Reads the scraped time limit (e.g. '2 seconds') from config.txt."""
    try:
        with open("config.txt") as f:
            text = f.read()
        match = re.search(r"([\d.]+)\s*second", text)
        if match:
            return float(match.group(1))
    except FileNotFoundError:
        pass
    print(f"⚠️  Couldn't read time limit from config.txt, defaulting to {default}s")
    return default


def run_stress_test(max_tests=1000):
    # 1. Compile the generator, brute force, and user's optimal solution
    compile_cpp("gen.cpp", "gen")
    compile_cpp("brute.cpp", "brute")
    compile_cpp("optimal.cpp", "optimal")

    time_limit = get_time_limit_seconds()
    # Give a buffer over the real limit since local hardware / -O2 vs CF's
    # judge can differ; this is for catching real infinite loops / bad
    # complexity, not for precise TLE judging.
    run_timeout = time_limit * 3

    print(f"✅ All files compiled successfully. Time limit: {time_limit}s (timeout set to {run_timeout}s)")
    print("Starting stress tests...\n")

    for i in range(1, max_tests + 1):
        # 2. Run generator. Pass the loop index 'i' as a seed for reproducible randomness
        with open("input.txt", "w") as f_in:
            subprocess.run(["./gen", str(i)], stdout=f_in)

        # 3. Run the brute force (correct) solution
        with open("input.txt", "r") as f_in, open("brute_out.txt", "w") as f_out:
            subprocess.run(["./brute"], stdin=f_in, stdout=f_out)

        # 4. Run the optimal (unverified) solution, with a timeout guard
        try:
            with open("input.txt", "r") as f_in, open("optimal_out.txt", "w") as f_out:
                subprocess.run(["./optimal"], stdin=f_in, stdout=f_out, timeout=run_timeout)
        except subprocess.TimeoutExpired:
            print(f"\n⏱️  TLE on Test {i}! (exceeded {run_timeout:.1f}s, limit was {time_limit}s)")
            print("--- Failing Input (truncated) ---")
            with open("input.txt", "r") as f_in:
                print(f_in.read()[:500])
            break

        # 5. Compare outputs ignoring trailing whitespace
        with open("brute_out.txt", "r") as f_brute, open("optimal_out.txt", "r") as f_opt:
            brute_ans = f_brute.read().strip()
            optimal_ans = f_opt.read().strip()

        if brute_ans != optimal_ans:
            print(f"\n❌ Wrong Answer on Test {i}!")
            print("--- Failing Input (truncated) ---")
            with open("input.txt", "r") as f_in:
                print(f_in.read()[:500])
            print("\n--- Brute Force (Expected) ---")
            print(brute_ans[:500])
            print("\n--- Optimal (Actual) ---")
            print(optimal_ans[:500])
            break
        else:
            # Overwrites the current line to prevent terminal spam
            print(f"✅ Test {i} Passed", end="\r")
    else:
        print(f"\n🎉 All {max_tests} tests passed with no mismatch found.")


if __name__ == "__main__":
    run_stress_test()