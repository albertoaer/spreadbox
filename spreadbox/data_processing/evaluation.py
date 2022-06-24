from types import FunctionType
from typing import Any, Tuple
from .queries import QueryMaker
from ..core.function_wrapper import FunctionWrapper, arg_wrap
from ..core.dependencies import DependencySolver

def eval_fn(name, src, wrapname, libs, env : Tuple[dict, dict]) -> FunctionWrapper:
    env = dict(env[0])
    for lib in DependencySolver.fromlist(libs):
        exec(str(lib), env, env)
    if wrapname:
        env[wrapname] = arg_wrap(src=src, wrapname=wrapname)
    exec(src, env, env)
    res = env[name]
    if not isinstance(res, FunctionWrapper):
        res = FunctionWrapper(res, src, wrapname=None)
    return res

def eval_from_query(type_ : str, value : dict, env : Tuple[dict, dict] = ({},{})) -> Any:
    val = None
    if type_ == 'function': val = eval_fn(value['name'], value['value'], value['wrapname'], value['libs'], env) 
    else: val = eval(value['value'])
    return val

def get_value_query(data : Any) -> Tuple[str, QueryMaker]:
    if isinstance(data, FunctionType): data = FunctionWrapper(data, wrapname=None)
    if isinstance(data, FunctionWrapper):
        return 'function', QueryMaker.function(data.name, repr(data), data.wrapname, data.libs)
    elif not callable(data):
        return 'literal', QueryMaker.literal(repr(data))
    else: raise Exception("Not supported yet")