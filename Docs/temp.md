# Variables and Data

_Railway_ variable are dynamically typed. This may not have been a good idea, but the language embraces runtime checks to enforce many of its properties, so dynamic typing does not ruin the narrative. There are only two data types: _numbers_ and _arrays_.

__Numbers__ are arbitrary-precision rationals, allowing multiplication / division to be first-class invertible operations alongside addition / subtraction. Floating-point arithmetic is a big no no for reversible computation due to the finite precision, and integer-only languages have restricted application. However, rational numbers do incur additional computational cost during all operations since once must find the irreducible form to prevent unnecessary memory growth.

__Arrays__ are lists of numbers or other arrays, and can contain mixed types. They are mutable, support indexed access / modification, and can change size by pushing to / popping from the end. All operations are constant time. 

There are 3 kinds of expression for creating arrays.

1. __Array Literals__

   Creates an array from an itemised list of contents. There is no aliasing in *Railway*, so any variables named in the array literal will by copied to the new array (e.g. below parts of A are copied into B twice, and A is not accessible via B).

   _Grammar:_

   ```EBNF
   "[" [expression] {"," expression} "]"
   ```

   _Examples:_

   ```railway
   let A = [1, 6, -3/5]
   let B = [[1, 2], 0, [], [A, A[1]]]
   ```

2. **Array Range**

   Creates an array using a starting number (included), stopping number (not included), and optional stepping number. Array ranges can be evaluated lazily when used to index for loops or try loops.

   _Grammar:_

   ```EBNF
   "[" expression "to" expression ["by" expression] "]"
   ```

   _Examples:_

   ```railway
   $ Creates [0, 1, 2, 3]
   let X = [0 to 4]
   
   $ Creates [10, 15/2, 5, 5/2]
   let Y = [10 to X[2] by -5/2]
   
   $ Lazy element evaluation in for loops avoids creating an array of size 100
   for (i in [0 to 100])
      println (i)
   rof
   ```

3. __Array Tensors__

   Creates a tensor (nested array of arrays) with dimensions specified by the second expression (which must be a 1D array of numbers). Places a copy of the first expression at every position in the new tensor.

   _Grammar:_

   ```EBNF
   "[" expression "tensor" expression ]"
   ```

   _Examples:_

   ```railway
   $ Create a 3x4 tensor of zeros (array of 3 arrays of 4 zeros each)
   let Z = [0 tensor [3, 4]]
   
   $ Copies Z into a 2x2 tensor, resulting in a 2x2x3x4 tensor of zeros
   let points = [Z tensor [2, 2]]
   ```

   

## Initialisation and Scopes

There are two scopes in _Railway_: global scope and function scope. 

**Global** variables are declared and initialised in global scope using the _global_ keyword at the file level, i.e. outside any functions. Global scope is evaluated when the file is parsed, and global variables are accessible from any function in the file. 

_Grammar_:

```EBNF
"global" name "=" expression
```

**Local** variables are declared and initialised in function scope using the _let_ keyword. 

_Grammar_:

```EBNF
"let" name "=" expression
```

Function scopes are flat: local variables declared at any level of 'indentation' in the function belong to the single function scope. Hence in the following example *x* and *array* are both in the same scope.

```railway
global N = 10

func myfunc()()
    let array = [0 to N]
    if (N > 20)
        let x = 4
		...
```

Variables in function scope can shadow global variables (be initialised with the same name). It is not possible to access the global variable from that scope until the local variable has been uninitialised.

**Variables may not go out of scope**. A variable going out of scope would destroy the information contained therein, which is not invertible; if the code was run in reverse and the variable reappeared in scope, the interpreter would not know how to initialise it. Therefore, if a function returns and there are still local variables in scope (which are not borrowed and not returned), a _LeakedInformation_ error is raised.

Since they cannot go out of scope, all local variables must be _uninitialised_ by value using the **unlet** keyword. This can be expensive, but ensures correctness. When code is reversed, **let** statements become **unlet** statements and vice versa.

```railway
let x = 6
x += 5
unlet x = 11
```

Does that mean I need to know the result of my program before it has run? Sort of, but also no. We'll get to that.



## Modifying Variables

For the same reason they can not go out of scope, you may not set the value of a variable which has already been initialised. The operation `x = 4` would not be invertible, since the previous value in x would be forgotten. This has profound consequences for the way _Railway_ programs are written, but that's not what this section is about. Here we discuss the ways an existing variable can be modified in place in an invertible fashion.

__Modifying Numbers__: There are four invertible operations that can be done in place on numeric variables. 

_Grammar_:

```EBNF
lookup ("+=" | "-=" | "*=" | "/=") expression
```

_Examples_:

```railway
x += 1
x -= 2
x *= 3
x /= 4
```

These work as expected, with the possible exception of Multiplication. In _Railway_, multiplying by 0 in place raises a _ZeroError_ because it is not invertible. When the code runs backwards, that 0 multiplication would be a 0 division, which should make you uncomfortable.

**Modifying Arrays**: Aside from modifying the numbers in the array using the above operations, there are the ___push___ and ___pop___ keywords.

_Grammar_:

```EBNF
"pop" lookup "=>" name
"pop" name "<=" lookup
"push" name "=>" lookup
"push" lookup "<=" name
```

Here _name_ means any legal variable name, and _lookup_ is a name and optionally some indices. The _pop_ statement removes the last element of the array specified by the _lookup_, and assigns it to the _name_ in the current scope. The _push_ statement removes the named variable from current scope and append it as an item on the end of the array specified by the lookup. This behaviour ensures that _push_ and _pop_ are mutual inverses, and prevents aliasing by making sure that that data pushed to an array cannot still be accessed via its old name. Whenever you see an arrow (`=>`) in _Railway_, it means an object is changing ownership, and you will no longer be able to access it under its old name.

_Examples_:

```railway
let X = [1,5,8,0]
pop X => value
$ Now 'X' is [1,5,8], 'value' is 0
value += 9
push value => X
$ Now 'value' is removed from scope, 'X' is [1,5,8,9]
```



### Self Modification & Aliasing

Self-modification is when information from a variable is used to modify that same variable. This is not allowed within a _Railway_ statement (though it is possible in other ways), since it is not in general invertible.

```railway
x /= x
```

Clearly the information in _x_ is destroyed here, so this code cannot be reversed. Below are more disallowed forms of self-modification, which will be caught a parse-time.

```
x += 
array[i] += array[j]
array[array[i]] += 1
```
