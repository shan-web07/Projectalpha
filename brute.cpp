#include <iostream>
#include <vector>

using namespace std;

void solve() {
    int n;
    cin >> n;
    vector<int> a(n);
    for(int i = 0; i < n; i++) {
        cin >> a[i];
    }
    
    // Write your naive, 100% correct brute-force logic here.
    // Example: Find the maximum sum of any pair (O(N^2) brute force)
    long long max_sum = -1e18;
    for(int i = 0; i < n; i++) {
        for(int j = i + 1; j < n; j++) {
            max_sum = max(max_sum, (long long)a[i] + a[j]);
        }
    }
    
    cout << max_sum << "\n";
}

int main() {
    // Standard fast I/O
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    int t;
    cin >> t;
    while(t--) {
        solve();
    }
    return 0;
}