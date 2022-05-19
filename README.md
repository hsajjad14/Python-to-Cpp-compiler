# Python-to-C++-compiler
A python to C++ compiler for a compilers course. The project description can be found here https://github.com/hsajjad14/Python-to-Cpp-compiler/blob/master/documentation/project-description.pdf. Uses the [ply](https://www.dabeaz.com/ply/) python library.

Sprint reports https://github.com/hsajjad14/Python-to-Cpp-compiler/tree/master/documentation.

To run, do: `python pythonCompiler.py <python_program>`. The python program must use indents and not spaces.

Example of a python program compiled to a executable C++ program:
```python
def fib(n: int) -> int:
        dp = [0,1]
        k = n+1
        i = 2
        first = 0
        second = 0
        while i < k:
                first = dp[i-1]
                second = dp[i-2]
                add = first + second
                dp.append(add)
                i+=1
        return dp[n]

x = fib(7)
print("the 7th fibonacci number is")
print(x)
```
The output is:
```cpp
#include <stdio.h>
#include <iostream>
#include <string>
#include <vector>
using namespace std;

int fib(int n) {
        vector<int> dp{ 0, 1, };
        int k = ((n + 1.0));
        int i = 2;
        int first = 0;
        int second = 0;
        while ((i < k)) {
                first = dp[(i - 1)];
                second = dp[(i - 2)];
                int add = ((dp[_t1] + dp[(first + second)]);
                dp.push_back(add);
                i = ((i + 1.0));
        }
        return dp[n];
}
int main() {
        int x = fib(7);
        cout << "the 7th fibonacci number is" << endl;
        cout << x << endl;
        return 0;
}
```
