import math
import operator
import sys

# parser

def tokenize(chars):
    chars = chars.replace('(', ' ( ').replace(')', ' ) ') #space oout parantheses
    chars = chars.replace("'", " ' ") # Space out quote 
    return chars.split() # Spit the input into a list of tokens 

def parse(tokens):
    if len(tokens) == 0:
        raise SyntaxError('Unexpected error End Of File') # no tokens are left
    token = tokens.pop(0) # Pop the first token 
    if token == '(':
        L = [] # start a new list
        while len(tokens) > 0 and tokens[0] != ')':
            L.append(parse(tokens)) # recursively parse the inner expressions
        if len(tokens) == 0: 
            raise SyntaxError('missing closing )') #error messafe for missing parathesis
        tokens.pop(0) # this is popping off ')'
        return L
    elif token == ')':
        raise SyntaxError('unexpected )') #unexpected closing paranthesis
    elif token == "'":
        return ['quote',parse(tokens)] # handles quote by convertung to quote...
    else:
        return atom(token) #parse as an atom
    

def atom(token):
    if token == 'T': #Constant T for true
        return 'T'
    elif token == 'NIL': # constand NIL for falsse
        return 'NIL'
    try:
        return int(token) #trying to converting token to integer
    except ValueError:
        try:
            return float(token)  #converting toekn to float
        except ValueError:
            return str(token)#else treating as a stirng

#environment
class Env(dict):
    def __init__(self, params=(), args=(), outer=None):
        super().__init__()
        self.update(zip(params, args)) #bind parameters to argument 
        self.outer = outer #link to pouter enviorment for scoping

    def find(self, var):
        if var in self:
            return self #variable found in current enviorment
        elif self.outer is not None:
            return self.outer.find(var) #look in outer enviorment
        else:
            raise NameError(f"undefined variable: {var}") # variable not found

#built-ins
def std_env():
    env = Env()
    env.update({
        '+' : lambda *x: sum(x), #sum
        '-' : lambda x, *y: x - sum(y), #subtract
        '*' : lambda *x: math.prod(x), #product of all 
        '/' : lambda x, y: x // y if y != 0 else exec('raise ZeroDivisionError("division by zero")'),
        '>' : lambda x, y: 'T' if x > y else 'NIL',
        '<' : lambda x, y: 'T' if x < y else 'NIL',
        '>=' : lambda x, y: 'T' if x >= y else 'NIL',
        '<=' : lambda x, y: 'T' if x <= y else 'NIL',
        '=' : lambda x, y: 'T' if x == y else 'NIL',
        '!=' : lambda x, y: 'T' if x != y else 'NIL',
        'and' : lambda *x: 'T' if all(x) else 'NIL',
        'or' : lambda *x: 'T' if any(x) else 'NIL',
        'not' : lambda x: 'NIL' if x == 'T' else 'T',
        'car' : lambda x: x[0],
        'cdr' : lambda x: x[1:],
        'cons' : lambda x, y: [x] + y,
        'sqrt' : lambda x: math.sqrt(x), 
        'pow' : lambda x, y: math.pow(x, y),
    })
    return env

#evaluator
def eval(x, env):
    if isinstance(x, str):# reference for variable
        if x in ('T', 'NIL'):  
            return x
        return env.find(x)[x]
    elif not isinstance(x, list):  # constant literal
        return x
    if len(x) == 0:
        raise SyntaxError('empty expression')

    if x[0] == 'quote':
        if len(x) != 2:
            raise SyntaxError(f"quote expects 1 argument, got: {x}")
        (_, exp) = x
        return exp
    elif x[0] == 'if':
        if len(x) != 4:
            raise SyntaxError(f"if expects 3 arguments: (if test conseq alt), got: {x}")
        (_, test, conseq, alt) = x
        exp = (conseq if eval(test, env) == 'T' else alt)
        return eval(exp, env)
    elif x[0] == 'define':
        if len(x) != 3:
            raise SyntaxError(f"define expects 2 arguments: (define var expr), got: {x}")
        (_, var, exp) = x
        env[var] = eval(exp, env)
        return var
    elif x[0] == 'set!':
        if len(x) != 3:
            raise SyntaxError(f"set! expects 2 arguments: (set! var expr), got: {x}")
        (_, var, exp) = x
        env.find(var)[var] = eval(exp, env)
        return var
    elif x[0] == 'defun':
        if len(x) != 4:
            raise SyntaxError(f"defun expects 3 arguments: (defun name (params) body), got: {x}")
        (_, name, params, body) = x
        def func(*args):
            local_env = Env(params, args, env)
            return eval(body, local_env)
        env[name] = func
        return name
    elif x[0] == 'lambda':
        if len(x) != 3:
            raise SyntaxError(f"lambda expects 2 arguments: (lambda (params) body), got: {x}")
        (_, params, body) = x
        return lambda *args: eval(body, Env(params, args, env))
    elif x[0] == 'mapcar':
        if len(x) < 3:
            raise SyntaxError(f"mapcar expects at least 2 arguments: (mapcar 'func list1 [list2 ...]), got: {x}")
        (_, func, *lists) = x
        fn_value = eval(func, env)
        if isinstance(fn_value, str):
            fn = env.find(fn_value)[fn_value]
        else:
            fn = fn_value
        eval_lists = list(map(lambda l: eval(l, env), lists))
        return list(map(fn, *eval_lists))
    else:
        proc = eval(x[0], env)
        args = [eval(arg, env) for arg in x[1:]]
        try:
            return proc(*args)
        except TypeError as e:
            raise TypeError(f"Function call error: {proc} with args {args} - {e}")

#repl
def repl(prompt='lispy>'):
    global_env = std_env()
    print("> Welcome to the fancy new Prompt LISP INTERPRETER, type in LISP commands! >")
    with open("results.file", "w") as output:
        while True:
            try:
                inp = input(prompt)
                if inp.strip().lower() in ('quit', 'exit'):
                    print("bye")
                    output.write("bye\nEnd Of File\n")
                    break
                tokens = tokenize(inp)
                parsed_exp = parse(tokens)
                val = eval(parsed_exp, global_env)
                if val is not None:
                    print(val)
                    output.write(str(val) + "\n")
            except Exception as e:
                print(f"Error: {e}")
                output.write(f"error: {e}\n")

if __name__ == '__main__':
    repl()
