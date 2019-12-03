# Mono Variables

Mono variables (read: mono-directional variables) are, depending on your perspective, an ugly experiment grafted onto the side of _Railway_ or a highly practical loosening of the belt in an otherwise suffocating language. Either way, as far as I know it has not been done before (probably for good reason), and therefore I thought it was worth trying.

As a motivating example, consider the following statement written in the father of all reversible languages, [Janus](http://tetsuo.jp/ref/janus.pdf "Janus: A Time-Reversible Language"). To be clear on terminology, the whole line below is a _statement_, and everything right of the `+=` is an _expression_. 

```Janus
x += 3 * y / 2
```

In Janus the only variable type is the 32-bit integer, which is a fairly sensible way of avoiding floating-point in a reversible language, but it means in-place division and multiplication (i.e. `\=` and `*=`) are not valid statements because integer division is not in general invertible. However, Janus does allow division and multiplication in expressions, as seen in the above expression `3 * y / 2`. Despite using a pure reversible language, we can use irreversible operators on the intermediate values that are composed into expressions. This is ok because when a statement is reversed the expressions are still run 'forwards', but the result is used differently (e.g. in the above example the expression is computed the same but then it is subtracted from `x` rather than added). That is to say, statements are the most granular reversible components in Janus, and everything below the level of statements need only be able to run forwards. Also in _Railway_, since self-modification [link] is not possible, the expression is guaranteed to have the same result both forwards and backwards. The question becomes, is it possible to extend the set of mono-directional things to include more than just expressions? Specifically, why should we not be allowed to break down the above Janus statement into multiple statements with temporary intermediate variables like below.

```railway
let temp = 3
temp *= y
temp //= 2  $ Integer division, non-invertible $
x += temp
```

This is doing the same thing, but in Janus and the pure part of _Railway_ it is not allowed because it is taking the "transient" things on which we are allowed to operate irreversibly and storing them into variables, which are somehow more concrete and therefore may not be subjected to irreversible operations. What has changed is that the interpreter no longer sees the intermediate values as things that are only needed when running forwards. All we need (sort of) is a way to mark variables like `temp` as _mono-directional_, things that are only computed forwards, and then a safe way of merging mono-directional information back with normal reversible information. People who have written C++ may draw parallels with rvalues; variables that behave as though they're still part of an expression even though they no longer are.

## Definition

_Grammar_ :

```EBNF
mono_name = "." name ;
promote_stmt = "promote" mono_name "=>" name
             | "promote" name "<=" mono_name ;
```

_Examples_:

```railway
let .tmp = 3 * y
.tmp //= 2
promote .tmp => tmp
x += tmp
```

Mono-directional variables, marked by names that start with a dot, are only declared and computed when the code is running forwards. When running backwards they do not exist. Information from a mono variable cannot affect non-mono variables: it must be promoted to a normal variable first using the _promote_ statement. When a promote statement is run backwards, the normal variable becomes mono and is therefore completely forgotten. This is ok, because we know the information will no longer be needed in the backwards direction, and can be safely derived again in the forwards direction.

Not letting information from mono-variables affect normal variables is very important, as that information won't be available when the code is running backwards. For a while I even considered calling these variables 'dirty' variables which must be 'cleaned' (rather than promoted) before interacting with normal invertible variables. This name very clearly conveyed the hierarchy, that clean information could be used anywhere but dirty information could only be used to affect other dirty information. The following are examples of illegal uses of mono variables, each of which will be caught at parse-time.

```railway
$ 1: Modifying non-mono variables using mono variables $
x += .y
push .y => array

$ 2: 'Destroying' information by moving it into mono variables $
unlet x = .y
push x => .array

$ 3: Mono information in condition affecting non-mono variables $
if (.y > 3)
    x += 1
fi ()
```

Eventually I went with the name _mono-directional_, because _dirty_ didn't really help understand another restriction on using this feature. Specifically, one cannot change the direction of time when mono-variables are in the current scope. The reason is fairly clear; though the interpreter would be quite capable of forgetting these variables when time swapped to going backwards, it would not be able to initialise them with the correct values if time swapped to going forwards at an arbitrary point in their lifetime. In practice, this only means that one cannot have any mono variables in scope at the start or end of the statement blocks in do-yield-undo and try-catch. Uncalling functions is fine because that direction change happens in another scope.

Integer division is not the only non-invertible operation that is possible in-place on mono variables. There is also pow, mod, logical xor, logical and, and logical or, using `**=`, `%=`, `^=`, `&=` and `|=` respectively. (If you hesitated when you read that logical xor is not invertible, recall that it is different from bitwise xor which I could not define on arbitrary precision rationals. Under logical xor, `54 ^ 0 = 1`, and we can't recover 54 from 1 using 0.) More importantly, we are not restricted to only non-invertible arithmetic operations. Mono variables are also allowed to silently pass out of scope since we don't need to know their final resting value in order to reinitialise them in reverse. Equally we may use assignment on a mono variable, i.e. override its old value with a new value. So in fact mono variables open up a whole new world of algorithms that were previously impossible in 'pure' _Railway_. I have attempted to illustrate this in the below 'case study'.

Finally, we briefly list the impact of mono variables on other _Railway_ structures.

1. As outlined in the Control Structures [link] page, the if statement, loop and for loop all become mono-directional if their forwards condition or forwards iterator contain mono variables. This means the entire control structure only runs when time is going forwards. Thus mono-directional control structures may not modify non-mono variables.

2. In order to check at parse time that a mono control structure is not modifying any non-mono variables (and bearing in mind that there is no parse-time linking) the parser must know from a function's call signature whether that function will modify any non-mono variables. Thus we introduce mono functions; a function is mono (modifies only mono variables and hence needn't be run at all if time is going backwards) if and only if its name begins with a dot, much like a mono variable. Proper use of a leading dot in a function's name is checked when the function is parsed.

   _Example_:

   ```
   func main(argv)()
       do
           let image = [[0,1,1,0], \
                        [1,0,0,1], \
                        [0,1,1,0]]
           call .draw2D(image)
       undo
   return ()
       
   func .draw2D(X)()               $ <- This is a mono function $
       for (.row in [0 to #X])     $ <- This is a mono for loop $
           for (.val in X[.row])   $ <- This is a mono for loop $
               if (.val)
                   print('X')      $ print isn't mono, but doesn't modify non-mono vars $ 
               else
                   print(' ')
               fi ()
           rof
           println('')  $ Newline $
       rof
   return ()
   ```



## Case Study: argmax

The argmax function takes a non-empty array and returns the index of the maximum element of that array. For example if `X = [2,3,91,5,4]`, then `argmax(X) = 2`. Consider how argmax might be implemented in another language like python (forgive the following example not being idiomatic python).

```python
def argmax(X):
    best_idx = 0
    for i in range(1, len(X)):
        if X[i] > X[best_idx]:
            best_idx = i
    return best_idx
```

How would we translate this into _Railway_? Firstly lets consider how to do it using only basic language features that are still Janus-like. The main problem is that this algorithm uses assignment; whenever a new best index is found, it is assigned to `best_idx` and the old best is forgotten. This is not an invertible statement. Therefore to make this algorithm reversible statement-by-statement, we end up having to store the intermediate best values into an array. 

```railway
func argmax(X)()
    let best_idx = 0
    let old_bests = []
    
    for (i in [1 to #X])
        if (X[i] > X[best_idx])
	        push best_idx => old_bests  $ Removes best_idx from scope $
	        let best_idx = i            $ Initialises a new best_idx $
	    fi (best_idx == i)
	rof
return (best_idx, old_bests)
```

This will not be a fun function to use, since it also returns an array of waste information (`old_bests`) to pollute the calling namespace. Most likely the only way to handle it will be to push it onto an ever growing global 'garbage' stack, which is the most inelegant way to make a program invertible. One obvious improvement allowed by a _Railway_-specific control structure would be to prevent this by wrapping the whole algorithm in a do-yield-undo to dismantle `old_bests` before returning.

```railway
func argmax(X)()
    do
        let best_idx = 0
        let old_bests = []
        for (i in [1 to #X])
            if (X[i] > X[best_idx])
	            push best_idx => old_bests
	            let best_idx = i
	        fi (best_idx == i)
	    rof  
	yield
	    let result = best_idx
	undo
return (result)
```

This is a pretty idiomatic _Railway_ function but it still has some issues, and foremost amongst them is memory complexity. In the worst case scenario where the elements of `X` are in strictly ascending order, the `old_bests` array will grow to the size of `X` (less one), which could be undesirable if `X` is large. The pure part of _Railway_ has another control structure that will let use trade in this memory complexity for compute complexity: the try-catch.

```railway
func argmax(X)()
    try (best_idx in [0 to #X])
        for (val in X)
            catch (val > X[best_idx])
        rof
    yrt
return (best_idx)
```

That's right. We use try to _guess_ what the correct index is, then catch any incorrect guesses. When the try passes, the state of the interpreter is as though we guessed the correct `best_idx` first time. This algorithm has constant memory complexity (since the range `[0 to #X]` is evaluated lazily), but instead we have compute complexity of the square of the size of `X`. By many conventional metrics this was a bad trade, but lets not forget that in reversible computing we're interested in quantum compute. Maybe qubits (memory) are expensive but superposition (parallelised compute?) is cheap? Who knows. Whether it's a good idea or not, I like this application of the try-catch.

Of course, neither of the proposed algorithms is as efficient as the python one using assignment. Fortunately, now that we have defined mono variables we have a third option available to us in _Railway_.

```railway
func argmax(X)()
    let .best_idx = 0
    for (.i in [0 to #X])
        if (X[.i] > X[.best_idx])
            let .best_idx = .i
        fi ()  
    rof
    promote .best_idx => best_idx
return (best_idx)
```

Mono variable `.best_idx` supports assignment, so we can write an algorithm exactly like the python one, with an extra step to promote the mono variable to a normal return result. This function is still invertible, because the inverse of computing the argmax is to forget the argmax. All we've done is made the interpreter do that forgetting a little earlier in the reversed code (when the promote statement runs backwards), so that the forwards algorithm can be much leaner. No information is lost; the argmax can still be deterministically derived in the forwards direction. Because the lifetimes of the mono variables are contained within this single function scope, it introduces no problems with reversing time for the caller. Note that both the for loop and if statement are mono-directional because they use mono iteration variables and conditions. This was not necessary, but it does mean that running this function backwards is literally doing nothing except consuming and uninitialising `best_idx`.

__Conclusion__: The mono implementation of argmax is clearly the superior, unless you consider mono variables to be offensive and ugly.