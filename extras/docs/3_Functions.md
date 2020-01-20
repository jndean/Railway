# Functions

Railway functions are declared at file level and become global symbols. There is no parse-time linking, so functions are looked up at run-time.

## Function Declarations

_Grammar_:

```EBNF
param_list = "(" [name] {"," name} ")" ;
function_decl = "func" name param_list param_list "\n"
                    {statement}
                 "return" param_list "\n" ;
```

_Example_:

```railway
func my_useless_function (array, thresh) (val)
    let i = 0
    loop (val > thresh)
        val /= 2
        i += 1
    pool (i > 0)
    push val => array
return (i)
```

_Railway_ function declarations are maybe a little unorthodox. They start with the _func_ keyword, have two lists of input parameters, have a body of statements, and have a list of output parameters after the _return_ keyword. Variables are exclusively passed by reference in _Railway_, because of what a headache it would be to properly clean up the copies created by passing by value in a system where they can't just fall out of scope. The reason for the two input parameter lists is that it corresponds visually much better to the way functions are called (see next section). The first parameter list is those variables that are passed to the function via a _borrowed_ reference, the second is the list of variables whose references are _stolen_ or _consumed_ by the function. When a function call consumes a reference it is removed from the calling scope and exists only in the called scope. It should then be disposed of before the end of the function, just like other locally declared variables. A borrowed reference is not removed from the calling scope, and may not be deallocated in any way by the borrower, so that it is still present in the borrowing scope at the function's end. Other than borrowed references, the only variables that may still be in scope at the end of the function are those that are to be returned. These will be moved to the calling scope upon return. 

To illustrate these roles, consider the _my_useless_function_ example above. It borrows references to _array_ and _thresh_, and steals a reference to _val_ (removing it from the calling scope), so all three are in scope at the function start. In the body statements _val_ is pushed onto _array_ and hence is no longer in scope. At the end of the function body the two borrowed variables are still in scope as required, and so is locally declared variable _i_, which is returned by the function and hence created in the calling scope. No other variables are still in scope at the end of the function.

Since functions only have one return point (I did not like the multiple return system in _Arrow_), when the function is called backwards (_uncalled_) the return values are instead stolen from the uncalling scope and the stolen inputs are instead returned to the uncalling scope as outputs, i.e. these two parameter lists swap roles. The borrowed references however have unchanged behaviour in reverse, and this is why such a distinction is made between borrowed and stolen inputs to functions. They are also made very visually distinct in the calling syntax.

## (Un)Calling a Function

_Simplified Grammar_:

```EBNF
func_call = [param_list "=>"] ("uncall" | "call") name param_list ["=>" param_list] "\n" 
          | [param_list "<="] ("uncall" | "call") name param_list ["<=" param_list] "\n";
```

(This grammar excludes call chaining and multithreaded calls to be a little bit clearer)

_Examples_:

```railway
$ Example 1: No consumed variables $
$ Borrows 'seed' and 'length', creates 'data' and 'key' $

call generate_data_and_key(seed, length) => (data, key)

$ Example 2: Call $
$ Consumes 'data', borrows 'key', creates 'encrypted' $

(data) => call encrypt(key) => (encrypted)

$ Example 3: Uncall $
$ Consumes 'encrypted', borrows 'key', creates 'data' $

(encrypted) => uncall encrypt(key) => (data)
```

I settled on this weird call syntax with arrows because with more traditional calls it was not very clear what information is being created and what is being consumed once you start making uncalls. This syntax is why the borrowed parameters are a distinct list to the stolen parameters in the function declaration; they are visually tightly bound to the function call, regardless of its direction, whereas the flow of data consumption / creation is separate. The flow needn't be left to right, you can write the arrows the other way around to get the opposite. If there are no stolen parameters or no return values, the corresponding brackets and arrow are optional (like example 1 above). This visual pipeline naturally lends itself to chaining function calls together; if the number of parameters created by one function matches the number consumed by another, the pipe may go directly from one to the other, and the intermediate variables never enter the calling scope. The below example is taken from _examples/processing.rail_.

```railway
(grid) => call serialise() > call RL.compress() > uncall decrypt(key) => (data)

println(data)

(data) => call decrypt(key) > uncall RL.compress() > uncall serialise() => (grid)
```

Note how the chains can mix calls and uncalls. Of course, what I really wanted was for the chaining arrows to be `=>` not `>`, but unfortunately this was not possible to parse with an LL(1) parsing algorithm. 

Function chains get long quickly, so now is a good time to mention that the _Railway_ lexer allows the escaping of newlines using `\`. Put these where you see fit, there are no formatting guidelines.

```railway
(grid) => call serialise()   \
        > call RL.compress() \
        > uncall decrypt(key)\
       => (data)

(grid) => call serialise()    \
         > call RL.compress()  \
          > uncall decrypt(key) => (data)
```



### Arguments

You have likely noticed that _Railway_ functions are only called with variable names as arguments, never with literals or array lookups. For example, all following are not valid arguments for a function call.

```railway
call myfunc(2, [0,0], array[0])
```

The justification for this is a bit patchy. 

1. Literals (like the literal number `2` and literal array `[0,0]` above) are not allowed because when passing by borrowed reference there needs to be something in the calling scope to which your reference refers. If there wasn't, any information you store into it will be lost when the called function ends. 
2. Array lookups (like `array[0]` above) are not allowed because when passing by stolen reference the referenced element would need to be removed from the array (to be properly stolen), and _Railway_ arrays are contiguous data structures which only allow insertion and deletion on the end.

Of course the remaining undiscussed combinations would be ok; it should be fine to pass literals for stolen references, and it would be ok to pass array lookups for borrowed references (as long as the same array wasn't used in any other argument lest there be aliasing). But for consistency (laziness) both of those cases are also disallowed. _Railway_ is a simplistic language, and in this case that means you sometimes need to spend a few lines giving function parameters their own named variable.

