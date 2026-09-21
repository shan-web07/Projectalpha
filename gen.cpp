#include <iostream>
#include <random>

using namespace std;

// Helper function to generate a random integer in range [a, b]
int rnd(int a, int b, mt19937& rng) {
    return uniform_int_distribution<int>(a, b)(rng);
}

int main(int argc, char* argv[]) {
    // 1. Catch the seed passed by tester.py
    int seed = atoi(argv[1]);
    mt19937 rng(seed);

    // 2. Generate problem constraints
    // Example: A test case with a number N, followed by an array of N integers
    int t = 1; // Number of test cases
    cout << t << "\n";
    
    while(t--) {
        int n = rnd(1, 10, rng); // Generate N between 1 and 10
        cout << n << "\n";
        
        for(int i = 0; i < n; ++i) {
            // Generate array elements between -100 and 100
            cout << rnd(-100, 100, rng) << (i == n - 1 ? "" : " ");
        }
        cout << "\n";
    }

    return 0;
}