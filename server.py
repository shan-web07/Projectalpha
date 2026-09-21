from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

import os
import re
import subprocess
import sys
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

APP_HOST = "127.0.0.1"
APP_PORT = 8080

# You can change this without editing the code:
# macOS/Linux:
#   export OPENAI_MODEL="gpt-5.6-luna"
#
# Windows PowerShell:
#   $env:OPENAI_MODEL="gpt-5.6-luna"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

# Automatically start tester.py after all required files
# have been generated and compiled successfully.
AUTO_START_TESTER = True

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# FLASK SETUP
# ============================================================

app = Flask(__name__)

# The extension is expected to send requests from Codeforces.
# We also allow localhost for easier local testing.
CORS(
    app,
    resources={
        r"/stress-test": {
            "origins": [
                "https://codeforces.com",
                "http://localhost:8080",
                "http://127.0.0.1:8080",
            ]
        }
    },
)


# ============================================================
# OPENAI SETUP
# ============================================================

try:
    client = OpenAI()
except Exception as e:
    client = None
    print("⚠️ OpenAI client could not be initialized.")
    print(f"   {e}")
    print("   Make sure OPENAI_API_KEY is set.")


# ============================================================
# HELPERS
# ============================================================

def clean_generated_code(text):
    """
    Removes markdown code fences if the model accidentally returns:

    ```cpp
    ...
    ```

    We want the actual C++ source only.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove ```cpp ... ```
    text = re.sub(r"^```(?:cpp|c\+\+|C\+\+)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return text.strip()


def call_openai(prompt):
    """
    Send a prompt to OpenAI and return plain text.
    """

    if client is None:
        raise RuntimeError(
            "OpenAI client is not initialized. "
            "Set OPENAI_API_KEY and restart server.py."
        )

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt,
    )

    text = getattr(response, "output_text", None)

    if not text:
        raise RuntimeError("OpenAI returned an empty response.")

    return text.strip()


# ============================================================
# GENERATE BRUTE FORCE SOLUTION
# ============================================================

def generate_brute(statement, samples):
    prompt = f"""
You are an expert competitive programmer.

Your task is to generate a BRUTE FORCE reference solution
for the Codeforces problem below.

IMPORTANT:
- Correctness is much more important than performance.
- The solution must be suitable for SMALL test cases.
- Use exhaustive search / enumeration / simple DP / recursion
  whenever appropriate.
- Do NOT implement the intended optimized solution unless
  brute force is the only practical way to verify correctness.
- The program must compile with GNU++17.
- Read input from stdin.
- Write output to stdout.
- Do not read or write files.
- Do not use interactive input.
- Do not print debugging information.
- Output ONLY valid C++ source code.
- Do NOT use Markdown fences.
- Follow the exact input/output format from the statement.

CODEFORCES PROBLEM:
-------------------
{statement}

SAMPLE INPUTS:
--------------
{samples}
"""

    code = call_openai(prompt)
    return clean_generated_code(code)


# ============================================================
# GENERATE TEST CASE GENERATOR
# ============================================================

def generate_generator(statement, samples):
    prompt = f"""
You are an expert competitive-programming test-data generator.

Generate a standalone C++17 program named gen.cpp for the
Codeforces problem below.

REQUIREMENTS:

1. The program must compile with GNU++17.
2. It must print exactly ONE complete valid test case to stdout.
3. It must accept an optional integer seed from argv[1].
4. Use deterministic randomness based on that seed.
5. If no seed is provided, use a reasonable default.
6. Every generated testcase MUST obey all constraints in the
   problem statement.
7. Do not generate invalid input.
8. Include a mixture of:
   - minimum-size cases
   - very small cases
   - boundary values
   - duplicate values where legal
   - sorted/increasing cases where applicable
   - decreasing cases where applicable
   - extreme values
   - adversarial structures
   - random cases
9. Since this generator is used for brute-force stress testing,
   KEEP GENERATED TESTS SMALL ENOUGH for brute.cpp to finish.
10. Prefer generating one carefully designed test case per run.
11. Output ONLY C++ source code.
12. Do NOT use Markdown fences.
13. Do not explain anything.
14. Do not depend on external libraries.
15. Use only standard C++17 libraries.

CODEFORCES PROBLEM:
-------------------
{statement}

SAMPLE INPUTS:
--------------
{samples}
"""

    code = call_openai(prompt)
    return clean_generated_code(code)


# ============================================================
# COMPILE C++ FILE
# ============================================================

def compile_cpp(source_filename, executable_filename):
    """
    Compile one C++ file with GNU++17.
    """

    source_path = BASE_DIR / source_filename
    executable_path = BASE_DIR / executable_filename

    if not source_path.exists():
        return False, f"{source_filename} does not exist."

    print(f"🔨 Compiling {source_filename}...")

    result = subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O2",
            str(source_path),
            "-o",
            str(executable_path),
        ],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )

    if result.returncode != 0:
        return False, result.stderr

    return True, ""


# ============================================================
# SAVE FILE
# ============================================================

def save_file(filename, content):
    path = BASE_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return path


# ============================================================
# OPTIONAL: START TESTER
# ============================================================

def start_tester():
    """
    Start tester.py in a separate process.

    We do not wait for it here because tester.py itself runs
    the stress-testing loop.
    """

    tester_path = BASE_DIR / "tester.py"

    if not tester_path.exists():
        print("⚠️ tester.py not found. Stress testing was not started.")
        return False

    print("🚀 Starting tester.py...")

    try:
        subprocess.Popen(
            [sys.executable, str(tester_path)],
            cwd=BASE_DIR,
        )

        print("✅ tester.py started.")
        return True

    except Exception as e:
        print(f"❌ Could not start tester.py: {e}")
        return False


# ============================================================
# MAIN API ENDPOINT
# ============================================================

@app.route("/stress-test", methods=["POST"])
def receive_data():

    print("\n" + "=" * 60)
    print("📥 New Codeforces request received")
    print("=" * 60)

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "status": "error",
            "message": "No JSON data received."
        }), 400

    # --------------------------------------------------------
    # Read data from extension
    # --------------------------------------------------------

    user_code = data.get("userCode", "")
    sample_inputs = data.get("inputs", [])
    sample_outputs = data.get("outputs", [])
    time_limit = data.get("timeLimit", "1 second")
    problem_statement = data.get("problemStatement", "")

    # Make sure values have sensible types
    if not isinstance(sample_inputs, list):
        sample_inputs = []

    if not isinstance(sample_outputs, list):
        sample_outputs = []

    if not isinstance(problem_statement, str):
        problem_statement = ""

    print(f"📄 Statement length: {len(problem_statement)} characters")
    print(f"🧪 Sample inputs: {len(sample_inputs)}")
    print(f"🧪 Sample outputs: {len(sample_outputs)}")
    print(f"⏱️ Time limit: {time_limit}")
    print(f"💻 User code received: {'Yes' if user_code else 'No'}")

    # --------------------------------------------------------
    # Validate statement
    # --------------------------------------------------------

    if not problem_statement.strip():
        return jsonify({
            "status": "error",
            "message": "Problem statement was not received."
        }), 400

    # --------------------------------------------------------
    # Save optimal.cpp
    # --------------------------------------------------------

    if user_code.strip():
        save_file("optimal.cpp", user_code)
        print("✅ Saved optimal.cpp")
    else:
        print("⚠️ No user code was received.")

    # --------------------------------------------------------
    # Save Codeforces samples
    # --------------------------------------------------------

    for i, sample in enumerate(sample_inputs):
        save_file(
            f"sample_{i + 1}.txt",
            str(sample)
        )

    for i, sample in enumerate(sample_outputs):
        save_file(
            f"sample_{i + 1}_out.txt",
            str(sample)
        )

    print(f"✅ Saved {len(sample_inputs)} sample input(s)")
    print(f"✅ Saved {len(sample_outputs)} sample output(s)")

    # --------------------------------------------------------
    # Save time limit
    # --------------------------------------------------------

    save_file("config.txt", str(time_limit))
    print("✅ Saved config.txt")

    # --------------------------------------------------------
    # Prepare samples for prompt
    # --------------------------------------------------------

    sample_text_parts = []

    for i, sample in enumerate(sample_inputs):
        output = ""

        if i < len(sample_outputs):
            output = sample_outputs[i]

        sample_text_parts.append(
            f"""
Sample #{i + 1}

INPUT:
{sample}

OUTPUT:
{output}
"""
        )

    samples_for_prompt = "\n".join(sample_text_parts)

    # --------------------------------------------------------
    # Generate brute.cpp
    # --------------------------------------------------------

    print("\n🤖 Generating brute.cpp...")

    try:
        brute_code = generate_brute(
            problem_statement,
            samples_for_prompt
        )

        if not brute_code.strip():
            raise RuntimeError("Generated brute.cpp is empty.")

        save_file("brute.cpp", brute_code)

        print("✅ Generated brute.cpp")

    except Exception as e:
        print(f"❌ Could not generate brute.cpp")
        print(f"   {e}")

        return jsonify({
            "status": "error",
            "stage": "generate_brute",
            "message": str(e)
        }), 500

    # --------------------------------------------------------
    # Compile brute.cpp
    # --------------------------------------------------------

    brute_ok, brute_error = compile_cpp(
        "brute.cpp",
        "brute"
    )

    if not brute_ok:
        print("❌ brute.cpp compilation failed:")
        print(brute_error)

        save_file(
            "brute_compile_error.txt",
            brute_error
        )

        return jsonify({
            "status": "error",
            "stage": "compile_brute",
            "message": "brute.cpp failed to compile.",
            "compiler_error": brute_error
        }), 500

    print("✅ brute.cpp compiled successfully")

    # --------------------------------------------------------
    # Generate gen.cpp
    # --------------------------------------------------------

    print("\n🤖 Generating gen.cpp...")

    try:
        gen_code = generate_generator(
            problem_statement,
            samples_for_prompt
        )

        if not gen_code.strip():
            raise RuntimeError("Generated gen.cpp is empty.")

        save_file("gen.cpp", gen_code)

        print("✅ Generated gen.cpp")

    except Exception as e:
        print(f"❌ Could not generate gen.cpp")
        print(f"   {e}")

        return jsonify({
            "status": "error",
            "stage": "generate_generator",
            "message": str(e)
        }), 500

    # --------------------------------------------------------
    # Compile gen.cpp
    # --------------------------------------------------------

    gen_ok, gen_error = compile_cpp(
        "gen.cpp",
        "gen"
    )

    if not gen_ok:
        print("❌ gen.cpp compilation failed:")
        print(gen_error)

        save_file(
            "gen_compile_error.txt",
            gen_error
        )

        return jsonify({
            "status": "error",
            "stage": "compile_generator",
            "message": "gen.cpp failed to compile.",
            "compiler_error": gen_error
        }), 500

    print("✅ gen.cpp compiled successfully")

    # --------------------------------------------------------
    # Compile optimal.cpp
    # --------------------------------------------------------

    if user_code.strip():

        optimal_ok, optimal_error = compile_cpp(
            "optimal.cpp",
            "optimal"
        )

        if not optimal_ok:
            print("❌ optimal.cpp compilation failed:")
            print(optimal_error)

            save_file(
                "optimal_compile_error.txt",
                optimal_error
            )

            return jsonify({
                "status": "error",
                "stage": "compile_optimal",
                "message": "optimal.cpp failed to compile.",
                "compiler_error": optimal_error
            }), 500

        print("✅ optimal.cpp compiled successfully")

    else:
        print("⚠️ optimal.cpp was not compiled because no user code was received.")

    # --------------------------------------------------------
    # Start tester
    # --------------------------------------------------------

    tester_started = False

    if AUTO_START_TESTER and user_code.strip():
        tester_started = start_tester()

    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE")
    print("=" * 60)
    print("✅ brute.cpp generated")
    print("✅ gen.cpp generated")
    print("✅ optimal.cpp saved and compiled")
    print(f"✅ tester.py started: {tester_started}")
    print("=" * 60 + "\n")

    return jsonify({
        "status": "success",
        "message": "Brute force and generator created successfully.",
        "brute_generated": True,
        "generator_generated": True,
        "optimal_saved": bool(user_code.strip()),
        "tester_started": tester_started
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "CF Tester server is running."
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CF Tester Server")
    print("=" * 60)
    print(f"📍 http://{APP_HOST}:{APP_PORT}")
    print(f"🤖 OpenAI model: {OPENAI_MODEL}")
    print(f"🧪 Auto-start tester: {AUTO_START_TESTER}")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️ WARNING: OPENAI_API_KEY is not set.")
        print("The server will start, but code generation will fail.")
        print()

    app.run(
        host=APP_HOST,
        port=APP_PORT,
        debug=False
    )