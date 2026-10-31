# catscript

```
 /\_/\
( o.o )   a programming language. for cats. sorry.
 > ^ <
```

catscript is a tiny programming language i made where you print with `cat`, write functions with `hunt`, and lists are called `litter`. if your code breaks, it insults you. if you use a dog word, it refuses to run.

**try it in your browser: [yupthatscole.github.io/catscript](https://yupthatscole.github.io/catscript)**

<img width="1919" height="958" alt="meow" src="https://github.com/user-attachments/assets/722cd2b8-925d-4ff0-abbb-3e85dc1d6d68" />
ignore my desktop pets...

```
hunt double(x) {
    bring x * 2
}

kittens = litter["mochi", "pip", "clover"]
cat("there are", size(kittens), "kittens")
cat("double 21 is", double(21))
```

```
there are 3 kittens
double 21 is 42

   /\_/\
  ( ^.^ )  purr. it worked.
   > ^ <
```

## running it

you need python 3. download this repo, then:

```
python catscript.py fizzbuzz.meow
```

catscript files end in `.meow`. it will not eat anything else.

## the language

| catscript | what it does |
|---|---|
| `cat(x)` | print something |
| `pspsps("name? ")` | ask the user for input |
| `name = "tuft"` | make a variable |
| `hunt f(x) { }` | make a function |
| `bring x` | return a value from a hunt |
| `litter[1, 2, 3]` | a list |
| `purr` / `hiss` | true / false |
| `empty_bowl` | nothing (null) |
| `if x > 3 { } else { }` | if / else |
| `for i in 1 to 10 { }` | count from 1 to 10 (both included) |
| `repeat 3 { }` | do something 3 times |
| `try { } pounce oops { }` | catch an error instead of crashing |
| `knock(x)` | knock a variable off the table (delete it) |
| `nap(2)` | sleep for 2 seconds |
| `size(x)` / `add(litter, x)` / `text(x)` | length, append, turn into text |
| `# hi` | comment |

`and`, `or`, `not`, `+ - * / %` and `== != < > <= >=` work like you'd expect.

### fizzbuzz

```
for i in 1 to 100 {
    if i % 15 == 0 {
        cat("FizzBuzz")
    } else if i % 3 == 0 {
        cat("Fizz")
    } else if i % 5 == 0 {
        cat("Buzz")
    } else {
        cat(i)
    }
}
```

## when things go wrong

errors have hiss codes, a line number, and an insult.

```
  HISS-404 (line 2): never heard of 'y'. did you make it up?
  did you write this while walking across the keyboard?

   /\_/\
  ( >.< )  HISS.
   > ^ <
```

| code | meaning |
|---|---|
| HISS-100 | catscript can't read a character |
| HISS-200 | the code is shaped wrong (missing `)` or `}`) |
| HISS-300 | wrong kinds of values, like `purr + 1` |
| HISS-403 | you used a dog word, or a name that's taken |
| HISS-404 | that name doesn't exist |
| HISS-406 | wrong number of things passed to a hunt |
| HISS-409 | `bring` outside a hunt |
| HISS-416 | no kitten at that litter position |
| HISS-500 | you divided by zero |
| HISS-508 | your cat is chasing its tail (a hunt called itself forever) |

### banned words

`fetch`, `bark`, `goodboy`, `woof`, `sit`, `wag`. this is a cat household.

```
  HISS-403 (line 1, col 1): 'fetch'?? this is a cat household.
```

## vs code extension

the `vs code` folder has an extension with syntax highlighting, a cat icon for `.meow` files, and a run button.

1. open vs code → extensions → `···` → **install from vsix...**
2. pick the `.vsix` file from the `vs code` folder
3. open a `.meow` file and press ▶ (or ctrl+shift+enter)

the run button looks for `catscript.py` in the same folder as your `.meow` file.

## how it works

it's written in python with no libraries, in three parts:

- **`lexer.py`** turns your code into tokens (`cat`, `(`, `"hi"`, `)`)
- **`parser.py`** turns the tokens into a tree, so it knows `1 + 2 * 3` means 2 × 3 first
- **`interpreter.py`** walks the tree and runs it

`catscript.py` ties them together and draws the cat. the playground runs the exact same python files in your browser using [pyodide](https://pyodide.org).
