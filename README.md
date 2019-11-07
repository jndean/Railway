# Railway
Railway is my attempt at a reversible imperative programming language. Its unique features (compared to reversible languages I have read about) include communicating multi-threading, mono-directional 'rvalue' variables, and the try-catch construct. In the interest of unrestricted experimentation some of the language's features are rather at odds with one another conceptually, however they are disjoint enough that there are very cohesive subsets.

This repository contains a very simple tree-walking proof-of-concept _Railway_ interpreter, placing a high emphasis on ensuring program correctness at run-time and completely disregarding performance (speed). A possible future project is to write a proper byte-code compiler, or devise an alternative dialect suitable for machine-code compilation.

### Influences

There are some very interesting reversible functional languages ([CoreFun]( http://hjemmesider.diku.dk/~robin/papers/rc2018.pdf "CoreFun"), [rFun]( https://github.com/kirkedal/rfun-interp "rFun")) but I came to reversible computation via an interest in turning back time, and functional languages don't care much for time so _Railway_ is imperative. Equally there are excellent explorations of reversible computation using OOP ([ROOPL]( https://pdfs.semanticscholar.org/f193/3ff3539aa785de9cbdc6edc80cf7335abb07.pdf "ROOPL"), [Joule]( https://www.researchgate.net/publication/304621348_Elements_of_a_Reversible_Object-Oriented_Language "Joule")), but I felt that the need to track each object's history so explicitly works against the goals of traditional OOP, so _Railway_ is not Object Oriented. Therefore, the two main influences for _Railway_ are [Janus](http://tetsuo.jp/ref/janus.pdf "Janus: A Time-Reversible Language") (the original reversible language) and [Arrow](https://etd.ohiolink.edu/!etd.send_file?accession=oberlin1443226400&disposition=inline "Arrow: A Modern Reversible Programming Language"). The former of course provides a skeleton of basic elements for the language, the latter provides inspiration for things like the do-yield-undo construct. Though you may see many arrow symbols (`=>`) in _Railway_ programs, this is actually part of the ownership system and bears no relation to the arrows in _Arrow_.

### Reversible Computation?

_Railway_ is a reversible language in the sense that any sequence of statements can be run both forwards and backwards deterministically, and hence so can any _Railway_ program. This might evoke for you the image of a train on a fixed set of tracks, along which it can move freely in either direction. There are two reasons we might be interested in reversibility:

1. __In theory__: A language in which every operation is invertible must necessarily be information-constant, that is it can not be possible to create or destroy information in any way. As silicon manufacturing processes get smaller and smaller, we become more and more concerned with the absolute physical limits of the technology. A process that destroys information is increasing entropy, and in turn is guaranteed to produce some quantity of heat (or maybe something else) no matter the design of the CPU. A process that uses a completely reversible model of computation need not increase entropy and so (in theory) has no guaranteed lower limit on the heat production. Of course nothing like that could be achieved by a reversible language such as _Railway_ being emulated by a non-reversible process on any current CPU, but studying reversible models of computation would be the first step on a path to understanding how to build such a system. 

   Also, people who talk about reversible programming languages sometimes talk about quantum computers, and I don't really know why.

2. __In Practice__: A language in which any set of instructions can be run backwards provides great opportunity for experimenting with novel control structures and techniques. For example, if you have written a (lossless) compression function in _Railway_ you get the corresponding decompression function for free because said function can be run backwards.

   ```railway
   (data) => call compress() => (compressed_data)
   (compressed_data) => uncall compress() => (data)
   ```

   As another example, the try-catch construct makes several attempts to run a block of code with different initial conditions provided by an iterator. Any time a catch happens, the interpreter reverts the state of the program back to the beginning of the try block by running the relevant lines backwards, then reattempts the try with the next initial condition.

   ```railway
   try (step_size in [1 to 0.1 by -0.1])
       call step_simuation(state, step_size) => (error)
       catch (error > epsilon)
   yrt
   ```

   For more examples, you'll have to read the full documentation.