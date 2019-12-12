# Parallelism

I have not yet encountered a reversible programming language that supports multi-threading. When we're interested in designing processes that can be reversed deterministically it makes sense to first restrict our attention to processes that can at least be run forwards deterministically, and multi-threaded applications generally do not fall into that category. I do remember reading somewhere about a language that could interleave instructions at compile time, but I'm talking about _parallelism_, not _concurrency_. What would that look like? I took a myopic approach to designing multi-threading in _Railway_, adding whatever made sense as it occurred to me once the single-threaded language design was finished. The resultant system is pretty lousy and doesn't properly explore the possibilities afforded by _Railway_'s unnecessarily strict "ownership" system, but it _is_ true parallelism in a reversible language. The bar wasn't set very high.

## Parallel Calls

_Grammar_:

```EBNF
parallel_call = ("call" | "uncall" ) name "{" expression "}" "(" param_list ")" ;
thread_id = "TID" ;
num_threads = "#TID" ;
```

_Example_:

```railway
func say_hi()()
    println("Hi, I am thread", TID + 1, "of", #TID)
return ()

func main(argv)()
    let x = 2
    call say_hi{x + 3}()
    unlet x = 2
return ()

$
Prints:
Hi, I am thread 1 of 5
Hi, I am thread 2 of 5
Hi, I am thread 3 of 5
Hi, I am thread 4 of 5
Hi, I am thread 5 of 5
$
```

Multi-threading is done by launching multiple parallel copies of a function, with as many threads as stated by the expression in curly braces after the function's name. You can use this call syntax to start a multi-threaded version of any _Railway_ function (as long as the arguments are compatible). These parallelised function calls create a _parallel context_ containing one scope for each spawned thread. Within a parallel context launched with n threads (n=5 in the above example), the threads have ids from 0 to n-1, and each may access its id via the `TID` keyword. Threads may access the value of n via the `#TID` keyword. Both `TID` and `#TID` evaluate to -1 if used outside of a parallel context. Parallel contexts are inherited by further function calls (so you can access `TID` in functions called within a parallelised call), unless those subcalls are themselves parallelised in which case they start their own new parallel context, run to completion, and then return to the current context. From within the current scope there is no way to tell whether your current parallel context was launched within another; all a thread can know is its id within the current context.

## Parallel Arguments

Arguments can be passed to parallel calls as normal.

```railway
(consumed_var) => uncall myfunc{nthreads}(borrowed_var) => (returned_var)
```

In the case of borrowed references, the behaviour is unchanged from a normal function call. Every copy of the called function has access to the borrowed variable and may not remove it from scope. Stolen/returned variables (two sides of the same coin when you can reverse your language) however, have modified behaviour. Allowing all called scopes to get copies of the stolen reference would have two possible implementations. 

1. All of those stolen references still refer to the same variable. This would be very awkward. It would be sort of like another borrowed reference in terms of how careful you would have to be when modifying it, but you'd also have to have a special uninitialisation mechanism that made sure all threads had finished with it and, when reversed, created something local to every thread. No way we're doing that.
2. The reference is stolen by thread 0, and all other threads get copies of the variable. This is a one-to-many operation, meaning the operation of a function returning a value (i.e. stealing in reverse) is many-to-one. What if not every thread agrees on the returned value? This is not invertible!

In short, we do not give stolen references to every thread. Instead, parallelised functions are _vectorised_ over the inputs/outputs. That is, all stolen inputs to a function should be arrays with as many elements as there are threads in the parallel call, and thread `j` will receive element `j` of the input as the stolen parameter. Similarly, all the items returned by a function called with `n` threads will be arrays of size `n` collecting together the `n` individual results of each thread. This is the exact inverse of stealing references, so parallel function calls can still be called and uncalled and chained together like (and with) normal function calls.

```railway
func zip()(x, y)
    let pair = []
    push x => pair
    push y => pair
return (pair)

func main(argv)()
    let X = [1, 2, 3, 4]
    let Y = [10, 20, 30, 40]
    (X,Y) => call zip{4}() => (Z)
    unlet Z = [[1,10], [2,20], [3,30], [4,40]]
return ()
```

Here two lists are zipped together into a single list of pairs. Four threads are launched in the call to zip, each consumes one element from both `X` and `Y`, and returns them paired up. All four resulting pairs are collected into array `Z`.

## Inter-Thread Communication

I've tried out two synchronisation primitives in _Railway_, an n-way _barrier_ and a _mutex_. Local instances of both can be given names, and both interact with every other primitive of the same name and type within the current parallel context.

### Barrier

A simple barrier construct, for making a thread wait at a named barrier until every other thread in the same parallel context has reached a barrier of the same name.

_Grammar_:

```EBNF
barrier_stmt = "barrier" STRING ;
```

_Example_:

```railway
func myfunc()()
    println("1")
    println("2")
    barrier "mybarrier"
    println("3")
    println("4")
return ()

func main(argv)()
    call myfunc{3}()
return ()

$
Prints:
1 2 1 2 1 2 3 4 3 4 3 4 
$
```

This construct is used exactly how it would be used in a normal program, for example to ensure all threads have added their result to a shared answer before any threads use that answer. A barrier is its own reverse, and will naturally cause the synchronisation points in reverse to be the same as they were going forwards. This is a good step towards deterministic reversibility.

### Mutex

The only way threads can exchange information is by reading and writing to variables borrowed from outside their shared parallel scope. Mutexes are used to address the classic issue of asynchronous modification by creating named blocks of code and only allowing a single thread to be in any blocks with the same name at any one time.

_Grammar_:

```EBNF
mutex_stmt = "mutex" STRING "\n"
               {statement}
             "xetum" "\n" ;
```

_Example_:

```railway
func main(argv)()
    let rectangles = [[3,5], [2,2], [7,5], [3,3]]
    let mean = 0
    call mean_area{#rectangles}(rectangles, mean)
return ()

func mean_area(rectangles, mean)()
    do
        let r = rectangles[TID]
        let area = r[0] * r[1]
    yield
        mutex "sum"
            mean += area
        xetum
    undo
    
    barrier "normalise"
    if (TID==0)
        mean /= #TID
    fi ()
return ()
```

In the above example, a mutex is used to ensure the integrity of the `+=` operation, which involves a read and write which must not be interleaved with the same read+write from any other thread. It also uses a barrier to ensure that the whole sum has been computed before thread 0 divides through by the number of rectangles.

The way a mutex in _Railway_ differs from a mutex you might be familiar with is that is also enforces the _order_ in which threads run the wrapped code block. For deterministic reversibility, when we have multiple threads mutating shared state we must ensure that when the program is reversed those mutations happen is reverse order. The most flexible implementation of this would record the order the operations happened forwards and then enforce the reversed order backwards. This is obviously infeasible because mutexes could be within loops of arbitrary length. I think it would not have been unreasonable for a mutex to have a forwards and backwards expression (like a _Railway_ if statement has a forwards and backwards condition) that specified which thread could enter the mutex next in either direction of time. However this actually relies on an assumption that all threads take the same path through the code and flip the direction of time at the same points. What if thread 2 passes through mutex A and then specifies that the 'next' thread should be 3 and the 'previous' thread should be 1. What if then thread 3 reaches the mutex with time going forwards and thread 1 reaches the mutex with time going backwards. Both should be allowed through, and we would have a race condition where the outcome depends on which thread gets there first. 

To avoid this, mutexes in _Railway_ have predetermined access order; threads must pass through in order of ascending thread number when time is going forwards, and in descending thread order when time is going backwards. Threads must pass through in blocks going in the same direction, and in practice that direction is determined by the first thread that arrives at the mutex. Once all threads have passed through in the given direction, the state of the mutex is reset and the direction for the next block of passes will be determined by the next arriving thread. 

This sounds like it should introduce the same race condition but it does not; if two threads approach the mutex with different time directions the mutex will see the second one as going the wrong way, whereupon it will raise a MutexError and bring the whole program down by triggering Sympathetic Errors in sibling threads (remember in _Railway_, errors are used to guarantee reversibility and help debugging by killing the interpreter whenever an illegal program is detected at runtime, and they are not intended to be "handled" by the program). Therefore it doesn't actually matter which thread arrives first.

Thanks to the mutex's direction errors, there can be no race conditions __so long as you wrap modification of shared data in mutexes__. It wouldn't be too difficult to enforce this at parse time if it weren't for the fact that from a function's definition alone the parser cannot know whether it will be called normally or vectorised over threads, and we shouldn't force a non-parallelised function to use mutexes. In hindsight it may have made sense for the declaration syntax to specify whether a function was for parallel or non-parallel calls, since functions that can usefully be called in both forms are rare and not especially valuable. As it is, parallelised _Railway_ only guarantees that code which runs forwards deterministically will run backwards deterministically. It is a clear departure from the language's identity and a sign of laziness that I didn't go back and implement the above change to ensure you can _only_ write parallel _Railway_ code which runs forwards deterministically.