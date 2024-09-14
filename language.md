## Language Description

The language is a **quantum while language**.

### Key Grammar Components

#### Variable Declarations (`decl`)
Variables are declared using the following syntax:

```
[variable1, variable2, ...]
```

For example:
```
[q1, q2, q3]
```

This declaration defines a list of variables that can be used in subsequent instructions.

#### Basic Commands (Simple Statements)
The language includes several commands to perform specific operations, each followed by one or more variables in parentheses:

- **input**: Requests input for a variable.  
  Syntax: `input(variable)`
  
- **h**: Executes the Hadamard operation on a variable.  
  Syntax: `h(variable)`
  
- **t**: Applies the T operation to a variable.  
  Syntax: `t(variable)`
  
- **x**: Applies the X (or NOT) operation to a variable.  
  Syntax: `x(variable)`
  
- **cx**: Performs the CNOT operation between two variables (control and target).  
  Syntax: `cx(variable1, variable2)`
  
- **skip**: Skips execution (similar to `pass` in Python).  
  Syntax: `skip`
  
- **m**: Measures a variable.  
  Syntax: `m(variable)`
  
- **z**: Applies the Z operation to a variable.  
  Syntax: `z(variable)`

#### Control Flow (Compound Statements)
The language also supports control constructs such as conditions and loops:

- **if**: Executes the block of instructions if thethe measurement of the specified variable is 1. An optional `else` block can also be defined.  
  Syntax:
  ```
  if variable:
      <instructions>
  else:
      <instructions>
  ```

- **while**: Executes a loop as long as the measurement of the specified variable is 1.  
  Syntax:
  ```
  while variable:
      <instructions>
  ```

- **loop**: Executes an indefinite loop. This instruction allows us to represent classical loops, such as a for loop.  
  Syntax:
  ```
  loop:
      <instructions>
  ```
