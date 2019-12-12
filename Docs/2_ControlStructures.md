# Control Structures

Some of _Railway's_ more exotic control structures such as the try-catch and the do-yield-undo explicitly make use of the language's ability to turn back time, whilst others such as the loops and if statements may seem more mundane due to their apparent familiarity. However, all of the constructs covered here require fresh attention when implemented in a reversible language.

## For Loop

_Grammar_:

```EBNF
for_stmt = "for" "(" name "in" expression ")" "\n"
               {statement}
           "rof" "\n" ;
```

Here the expression should evaluate to an array (called the iterator in this context, even though it's still just an array). For each element in the iterator, the contents will be copied (to prevent [aliasing](1_VariablesDataAndScope.md/#self-modification-&-aliasing)) into a local variable with the specified name (called the iteration variable), and the code block will be run, much like a normal for loop. At the end of the loop, the iteration variable will be deallocated correctly even if the contents of the iterator have been modified. 

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
loop_stmt = "loop" "(" expression ")" "\n"
                {statement}
            "pool" "(" [expression] ")" "\n" ;
```

The loop construct is the same as a traditional while loop, running the block of statements on a loop until the forward condition (the first expression) stops evaluating to True. In reverse, it will run the block backwards until the backwards condition (the second expression) stops evaluating to True. It is insufficient to use only the first expression, because by definition it will not distinguish when to stop running the loop in reverse. Consider the below example from another language:

```python
n = 10
while (n > 1):
    n /= 2
```

There is no way to tell from the condition `n > 1` when to exit the loop in reverse, i.e. when `n = 10`. Hence _Railway_ requires the second 'backwards' condition in a loop. 

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
if_stmt = "if" "(" expression ")" "\n"
              {statement}
          ["else" "\n" 
              {statement}]
          "fi" "(" [expression] ")" "\n" ;
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

```EBNF
doyieldundo_stmt = "do" "\n"
                       {statement}
                   ["yield" "\n"
                       {statement}]
                   "undo" "\n" ;
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

This is a good convenience feature, however it has two major drawbacks; copy-return functions are unable to have side-effects (they just get undone), and it doesn't have much granularity unless you make lots of tiny functions. Before I came to implement copy-return I read about the do/undo-yielding control structure in [Arrow](https://etd.ohiolink.edu/!etd.send_file?accession=oberlin1443226400&disposition=inline "Arrow language"), and decided this was a more general tool that could also take the place of copy-return.

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

Also, I was originally going to allow only a 'yieldable' subset of statements in yield blocks, specifically I was going to try and make it impossible for the yield block to modify any variables that were used in the do block. This was to guarantee that the 'undo' would perfectly revert the state changes enacted by the 'do'. However, it wasn't clear what things should be yieldable, and I eventually decided this was because the restrictions were a bit meaningless. The do-yield-undo is just syntactic shorthand for applying a process, doing some work, then applying the process in reverse, which you can very well do by hand writing the undo statements. Thus the same mechanisms that prevent you from doing anything non-invertible in that situation will apply during the do-yield-undo, and if you manage to confuse yourself you should eventually hit something like an uninitialisation value error. For an example of a yield block that modifies variables used by the do block, see the 'transform' function in "examples/cellular_automaton.rail".



## Try and Catch

_Grammar_:

```EBNF
try_stmt = "try" "(" name "in" expression ")" "\n"
               {statement}
           "yrt" "\n" ;

catch_stmt = "catch" "(" expression ")" "\n" ;
```

In the try statement, the expression must evaluate to an array, here referred to as the iterator. Values are copied from the iterator into scope under the given name (called the iteration variable), and the statement block is run. The statement block should contain at least one catch statement. When a catch statement runs, if the expression (the condition) evaluates to False then it has no effect. If it evaluates to True, the preceding lines in the surrounding try block are reversed, taking the state of the scope back to where it was at the start of the try. Then the next value from the iterator is assigned to the iteration variable and the try block tries again. At least one value in the iterator should pass the try block without catching, otherwise an _ExhaustedTry_ error is raised. When the try block runs to completion without catching, the try statement is over and __the iteration variable is left in scope__. This is necessary otherwise it may not be possible to determine after-the-fact which code path was taken through the try, and hence the try statement would not be invertible. When a try statement is reversed, since the passing iteration variable is already in scope, all it does is run the statement block backwards one time ignoring catch statements, then _in theory_ uninitialises the iteration variable and exits. In practice the reverse behaviour is slightly different, but first we should check out some examples.

_Examples_:

```railway
$ Example 1: adjust step size in simulation, with minimum 1 $
try (step_size in [10 to 1 by -1])
    call step_simuation(state, step_size) => (error)
    catch (error > epsilon || step_size == 1)
yrt

$ Example 2 : argmax function (index of greatest element) $
func argmax(X)()
    try (max_i in [0 to #X])
        for (i in [0 to #X])
            catch (X[i] > X[max_i])
        rof
    yrt
return (max_i)
```

That argmax example may seem really dumb (it has time complexity `O(n^2)`) but I think it's one of the most interesting applications of the try and catch construct. See the [later discussion](4_MonoVariables.md/#case-study:-argmax) on the ways to implement argmax in _Railway_.

My motivation for the try-catch was quite obvious; everybody touts error recovery as a possible application of reversible computation, but I couldn't find anybody who actually tried it. I quickly ruled out catching runtime errors as in _Railway_ they're mostly used to prevent bad (non-invertible) programs, and I don't want the programmer to ever have an excuse to write those. Hence I settled with catching the result of programmer-given conditions, inserted at key moments in the statement block. Next, since the point is to use invertibility, I arrived at the design where any number of catches can trigger a reversal back to the starting state. I figured I needed to leave some variable in scope to record the code path taken (the other approach would have been to have a backwards condition like _Railway's_ if statement, but that would have ruled out having multiple catches in a try, plus the point is to explore something _different_), but dealing with that variable would always be awkward if that was all it did, so I eventually settled on it iterating over a user-provided array so that the persisting iteration variable has real meaning in the program's context. I think the final product is actually quite different from a normal try-catch, with broader applications.

So far I have only talked about an idealised try-catch, and if you write error-free _Railway_ code you'll likely not notice how it differs from what the interpreter actually does. However, the ideal version has two conceptual issues. Firstly, _Railway_ claims to be time-and-memory-linearly reversible. The try statement can run the try block forwards arbitrarily many times, but backwards it only runs the block once. In this case the reversal is fine, very sublinear in time complexity. However, if we have code that, as part of its forward run, _uncalls_ a function that contains a try, then we're in trouble because the time to run inverse-inverse try (i.e. try) is not linear in the time to run inverse try. The second issue is shown in the following example (if you are confused by talk of calls and uncalls below, you may want to reference the documentation on [functions](3_Functions.md).

```railway
func create_information()()
   try (garbage in [0 to 999])
       catch (garbage < 4)
   yrt
return (garbage)

func main(argv)()
    let x = 89
    (x) => uncall create_information()
return ()
```

The _create_information_ function tries many values for garbage, and as soon as it tries `garbage = 4` it passes and returns that value. However the reverse of _create_information_ accepts any variable and destroys it, assuming that it was created by a successful pass through the try. The _main_ function exploits this by uncalling _create_information_ and using it to uninitialise an arbitrary value (the reference to variable _x_ is stolen by the uncall), thus destroying information in a non-invertible fashion. Indeed if we were to try running main in reverse, we'd get value error when the code tried to unlet _x_ using 89, since it will have value 4. Fundamentally, the problem is that the idealised try statement does not check whether the value that it is given in reverse is the value that would pass running forwards. 

To solve both the above issues, the reverse of try initially behaves as previously described, running the statement block in reverse and so bringing the state of the scope to the point at the start of the try. It then runs the try forwards in its entirety,  and checks that the value that passes is the same one that was provided at the beginning of the reversal. Finally, it once again runs the statement block backwards, deallocates the iterator variable with the knowledge that it is correct, and exits. This clearly ensures that the try is invertible, and it also makes the backwards try time-linearly reversible (because now the backwards try takes a fixed amount of work more than the forwards try).