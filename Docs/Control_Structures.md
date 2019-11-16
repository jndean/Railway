# Control Structures

Some of _Railway's_ control structures may be familiar from other languages and some may seem more exotic, but all require fresh attention when implemented in a reversible language.

## For Loop

_Grammar_:

```EBNF
"for" "(" name "in" expression ")" "\n"
    {statement}
"rof" "\n"
```

Here the expression should evaluate to an array (called the iterator in this context, even though it's still just an array). For each element in the iterator, the contents will be copied (to prevent aliasing) into a local variable with the specified name (called the iteration variable), and the code block will be run, much like a normal for loop. At the end of the loop, the iteration variable will be deallocated correctly even if the contents of the iterator have been modified. 

When the code runs in reverse, the for loop runs over the iterator backwards, and runs the code block backwards. You may need to convince yourself that it is fine (deterministic, reversible) to use the same loop expression when going in reverse, even if the code block modifies the iterator's elements / length.

_Hints_: Because of the copying, it is recommended not to iterate over arrays with complex elements, and instead to iterate over indices and access the array within the code block. Also note that array ranges can be evaluated lazily, making them perfect as index generators for for loops.

_Examples_:

```railway
$ Iterate lazily over a range, doing a fibonaci calculation $
let a = 1
let b = 1
for (i in [0 to n])
    a += b
    swap a <=> b
    println(a, b)
rof


$ Iterate over points, modifying the iterator in the loop $
let points = [[0,1], [5,-2], [9, 0]]
for (point in points)
    if (point[0] < 3)
        let shifted_point = [point[0] + 3, point[1]]
        push shifted_point => points
    else
        println("x:", point[0], "y:", point[1])
    fi ()
rof
```

A for loop is mono-directional if the iterator is a mono variable. In this case, the for loop will only be run when the code is run forwards, and the loop body may not modify non-mono variables.



## Loop

_Grammar_:

```EBNF
"loop" "(" expression ")" "\n"
    {statement}
"pool" "(" [expression] ")" "\n"    
```

The loop construct is the same as a traditional while loop, running the block of statements on a loop until the forward condition (the first expression) stops evaluating to True. In reverse, it will run the block backwards until the backwards condition (the second expression) stops evaluating to True. It is insufficient to use only the first expression, because by definition it will not distinguish when to stop running the loop in reverse. Consider the below example from another language:

```python
n = 10
while (n > 1):
    n /= 2
```

There is no way to tell from the condition `n > 0` when to exit the loop in reverse, i.e. when `n = 10`. Hence _Railway_ requires the second 'backwards' condition in a loop. 

_Examples_:

```railway
let n = 10
loop (n > 1)
    n /= 2
pool (n != 10)

$ Take every element from input and put them in output $
let input = [1,3,5,6,8,9,0,4,2]
let output = []
loop (#input)
    pop input => val
    push val => outpupt
pool (#output)
```

When the code is run forwards, the following conditions are required:

1. The forwards condition is True before every time the statement block is run
2. The backwards condition is True after every time the statement block is run
3. The forwards conditions is False after the whole loop 
4. The backwards condition False before the whole loop starts

1 and 3 will obviously hold by the definition of a loop, but 2 and 4 will be explicitly checked by the interpreter at run-time to catch badly defined loop conditions that will behave differently in reverse. The natural opposite conditions are checked when the loop is runs backwards.

A loop is mono-directional if the forward condition contains a mono-directional variable. In this case it will only be run when the code is going forward, it may not modify any non-mono variables, and it may not specify a backwards condition (which is why the backwards condition is marked optional in the grammar, even though it is normally compulsory).



## If Statement

_Grammar_: 

```EBNF
"if" "(" expression ")" "\n"
    {statement}
["else" "\n" 
     {statement}]
"fi" "(" [expression] ")" "\n"
```

The if statement evaluates the first expression (the forwards condition), runs the first block of statements if it is true and runs the second block otherwise (if it is provided), just like a normal if statement. When running backwards the second expression (the backwards condition) is used instead. The evaluation of the forwards condition before the statement block runs must match the evaluation of the backwards condition after the statement block runs to ensure the code reverses properly, and this is checked explicitly by the interpreter at run-time much like the conditions in the loop construct. The backwards condition is necessary because when one of the blocks runs it may modify the state of the program in a way which changes the value of the forwards condition expression, and thus when entering the if statement in reverse it is not possible to know which code block to run using only the forwards condition.

_Example_:

```railway
ball_y += ball_speed_y
if (ball_y <= 0)
    $ Ball hit the floor, so bounce $
    ball_speed_y *= -1
    ball_y *= -1
fi (ball_y - ball_speed_y <= 0)
```

See that in this example `ball_y` will always be non-negative after the if statement, so the backwards condition must check if the ball hit the floor in a different way. Hence self-modification is possible (i.e. the change to `ball_y` is dependent on the value of `ball_y`) without destroying information. If the programmer tries to do something non-invertible using an if statement, they will find it impossible to write a backwards condition that passes the run-time checks, and thus the language still guarantees reversibility. 

Leaving the backwards condition brackets empty is a syntactic shorthand to imply that both conditions are the same, reducing typing and visual code clutter. Originally the way to do this was to omit the brackets as well, but I found this made it too easy to forget to consider the backwards condition at all, what with it being an unusual thing to need to consider. Having to type the empty brackets helps remind me that I am explicitly setting the backwards condition to be the same as the forwards condition.

An if statement is mono-directional if any mono variables are used in the the forwards condition, in which case it will only be evaluated when the code is running forwards. A mono if statement cannot modify any non-mono variables, and cannot have a backwards condition.



## Do-Yield-Undo

_Grammar_:

```
"do" "\n"
    {statement}
["yield" "\n"
    {statement}]
"undo" "\n"
```

When time is going forwards, this construct does three things in order:

1. Runs the first statement block (the do block) forwards
2. Runs the second statement block (the yield block) forwards (if it is provided)
3. Runs the do block backwards

The motivation for do-yield-undo comes from the importance of cleaning up after yourself in _Railway_, since variables cannot pass out of scope and hence must be uninitialised. The do block is used to compute short-lived variables, the yield block may make use of them, then the do block is reversed to uncompute them and remove them from scope at no mental cost to the programmer.

```railway
do
    let sum = 0
    for (x in X)
        sum += x
    rof
yield
    call furtherComputation(sum)
undo
```

When we introduced the need to _unlet_ all our variables explicitly by value, we noted that surely this would mean we need to know the results of all our computations ahead of time. It is by frequent use of do-yield-undo that we avoid this issue, using undo blocks to reverse the computation of variables and hence remove them from scope without knowing their end value whilst writing the program.

Originally this feature was going to be less general. I wanted to address the difficulties of cleaning up a function scope before returning, and so I introduced a 'copy-return' as an alternative to a return at the end of a function call. If a copy-return was used, the function would run forwards, copy the values to be returned out into temporary space, then run backwards, cleaning up everything in scope. For example:

```railway
$ VERSION 1 : NOT VALID RAILWAY CODE $
func myfunc(X, i, j, mu)()
	let sum = 0
    for (x in X)
        sum += x
    rof
    let a = (X[i] / sum) - mu
    let b = (X[j] / sum) - mu
    let result = (a*a + b*b) ** (1/2)
copyreturn (result)
```

This is a good convenience feature, however it has two major drawbacks; copy-return functions are unable to have side-effects (they just get undone), and it doesn't have much granularity unless you make lots of tiny functions. Before I came to implement copy-return I read about the do-yielding-undo control structure in [Arrow](https://etd.ohiolink.edu/!etd.send_file?accession=oberlin1443226400&disposition=inline "Arrow language"), and decided this was a more general tool that could also take the place of copy-return.

``` railway
$ VERSION 2 : VALID RAILWAY CODE $
func myfunc(X, i, j, mu)()
  do
	let sum = 0
    for (x in X)
        sum += x
    rof
    let a = (X[i] / sum) - mu
    let b = (X[j] / sum) - mu
  yield
    let result = (a*a + b*b) ** (1/2)
  undo
return (result)
```

Also, I was originally going to allow only a 'yieldable' subset of statements in yield blocks, specifically I was going to try and make it impossible for the yield block to modify any variables that were used in the do block. This was to guarantee that the 'undo' would perfectly revert the state changes enacted by the 'do'. However, it wasn't clear what things should be yieldable, and I eventually decided this was because the restrictions were a bit meaningless. The do-yield-undo is just syntactic shorthand for applying a process, doing some work, then applying the process in reverse, which you can very well do by hand writing the undo statements. Thus the same mechanisms that prevent you from doing anything non-invertible in that situation will apply during the do-yield-undo, and if you manage to confuse yourself you should eventually hit an uninitialisation value error. For an example of a yield block that modifies variables used by the do block, see the 'transform' function in "examples/cellular_automaton.rail".