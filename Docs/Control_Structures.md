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
points = [[0,1], [5,-2], [9, 0]]
for (point in points)
    if (point[0] < 3)
        shifted_point = [point[0] + 3, point[1]]
        push shifted_point => points
    else
        println('x:', point[0], 'y:', point[1])
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

The if statement evaluates the first expression (the condition), runs the first block of statements if it is true and runs the else block otherwise (if it is provided), just like a normal if statement. When one of the code blocks runs it may modify the state of the program in a way which changes the value of the condition expression, necessitating a backwards condition. The evaluation of the forwards condition before the statement block runs must match the evaluation of the backwards condition after code block runs, and this is checked explicitly by the interpreter at run-time as with the loop conditions. 

```railway
ball_y += ball_speed_y
if (ball_y <= 0)
    $ Bounce
    ball_speed_y *= -1
    ball_y *= -1
fi (ball_y - ball_speed_y <= 0)
```

In this way, self-modification is possible (i.e. the change to `ball_y` is dependent on the value of `ball_y`) without destroying information. 