# G1 source projection audit — 26 October 2026

Status: `CODE_CREATED_NOT_EXECUTED`; `WORK_COMPLETE_PENDING_REVIEW`.
This is a non-executing source comparison, not a numerical or behavioral test.
The code below was executed only as a stdlib AST/read-only-Git audit against the
uncommitted source bytes identified in `g1_static_validation.json`. It never imports
APEX, the recorder, launcher or tests. Ruff also inspected/formatted those files statically.

OFF normalization selects original branches, removes the optional recorder argument,
its stored alias, and the new `sys.exc_info` import. All six complete modules then
match the authorized base AST exactly, including original clocks, numerical statements,
catch classes and scheduler consumer.

ON normalization additionally removes named observation statements/finally blocks,
restores original return/tuple bindings and reverses the single solver-constructor
hoist in `make_mpc`. All six modules match the base AST. The new observer-fault stops
are deliberately excluded from this projection and inspected separately against the
approved startup/end-of-release boundaries. They are not a full-trace parity claim.

The script's removal rules are visible below; this is a design audit with explicit
normalizations, not an executable proof of exception safety or one-time runtime
execution. Host overhead naturally affects legacy measured durations. G2 must test
numerical values, actual call counts/order, failures, warm resets, RK4 and authority.

```python
import ast, json, subprocess, hashlib
from pathlib import Path
ROOT=Path.cwd()
BASE='83f360b2a96e8f6d9fe429d2cc2e5447da2f47c8'
manifest=json.loads((ROOT/'docs/task007f/profile1/g1_source_change_manifest.json').read_text())
paths=manifest['future_runtime_and_test_allowlist'][:6]
def dump(n): return ast.dump(n,include_attributes=False)
class Off(ast.NodeTransformer):
    def visit_ImportFrom(self,n):
        return None if n.module=='sys' and [a.name for a in n.names]==['exc_info'] else n
    def visit_arguments(self,n):
        for i in range(len(n.kwonlyargs)-1,-1,-1):
            if n.kwonlyargs[i].arg=='recorder':
                n.kwonlyargs.pop(i);n.kw_defaults.pop(i)
        return n
    def visit_Assign(self,n):
        if any(isinstance(t,ast.Attribute) and t.attr=='_recorder' for t in n.targets): return None
        if len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='recorder': return None
        return self.generic_visit(n)
    def truth(self,n):
        if isinstance(n,ast.Compare) and isinstance(n.left,ast.Name) and n.left.id=='recorder' and len(n.ops)==1 and isinstance(n.comparators[0],ast.Constant) and n.comparators[0].value is None:
            if isinstance(n.ops[0],ast.Is):return True
            if isinstance(n.ops[0],ast.IsNot):return False
        if isinstance(n,ast.BoolOp) and isinstance(n.op,ast.And):
            if any(self.truth(v) is False for v in n.values):return False
        return None
    def visit_If(self,n):
        value=self.truth(n.test)
        if value is not None:
            out=[]
            for s in (n.body if value else n.orelse):
                x=self.visit(s)
                out.extend(x if isinstance(x,list) else [x] if x is not None else [])
            return out
        return self.generic_visit(n)
results={}
for path in paths:
    before=ast.parse(subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT))
    after=Off().visit(ast.parse((ROOT/path).read_text()))
    same=dump(before)==dump(after)
    results[path]=same
    if not same:
        import difflib
        print(path)
        print(''.join(difflib.unified_diff(ast.unparse(before).splitlines(True),ast.unparse(after).splitlines(True)))[:8000])
print(json.dumps(results,indent=2))
class On(Off):
    def __init__(self): self.values={}
    def visit_FunctionDef(self,n):
        old=self.values; self.values={}
        n=self.generic_visit(n)
        if n.name=='make_mpc':
            # Reviewed hoist of one nested solver constructor; same position before controller.
            statements=n.body
            assign=next(x for x in statements if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='solver' for t in x.targets))
            expression=assign.value
            class Inline(ast.NodeTransformer):
                def visit_Name(self,node):
                    return expression if node.id=='solver' and isinstance(node.ctx,ast.Load) else node
            n=Inline().visit(n)
            n.body.remove(assign)
        self.values=old
        return n
    def visit_If(self,n):
        if isinstance(n.test,ast.BoolOp) and any(isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute) and isinstance(v.func.value,ast.Name) and v.func.value.id=='recorder' for v in n.test.values):
            return [] # Added observer fault reporting stops, separately audited.
        v=self.truth(n.test)
        if v is not None:
            out=[]
            for s in (n.orelse if v else n.body):
                x=self.visit(s);out.extend(x if isinstance(x,list) else [x] if x is not None else [])
            return out
        return self.generic_visit(n)
    def visit_Call(self,n):
        n.keywords=[k for k in n.keywords if k.arg!='recorder']
        return self.generic_visit(n)
    def visit_Expr(self,n):
        if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='recorder':return None
        return self.generic_visit(n)
    def visit_Assign(self,n):
        t=n.targets[0] if len(n.targets)==1 else None
        if isinstance(t,ast.Attribute) and t.attr=='_instrumentation_last_preparation':return None
        if isinstance(t,ast.Name) and t.id=='_g1_prepared':
            names=('startup','startup_event') if any(k.arg=='startup' for k in n.value.keywords) else ('packet','event')
            return ast.Assign(targets=[ast.Tuple(elts=[ast.Name(id=x,ctx=ast.Store()) for x in names],ctx=ast.Store())],value=self.visit(n.value))
        if isinstance(n.value,ast.Name) and n.value.id=='_g1_prepared':return None
        if isinstance(t,ast.Name) and t.id.startswith('_g1_'):
            if t.id.startswith('_g1_value_'):self.values[t.id]=self.visit(n.value)
            return None
        return super().visit_Assign(n)
    def visit_Name(self,n):
        return self.values.get(n.id,n) if isinstance(n.ctx,ast.Load) else n
    def visit_Try(self,n):
        observation_final=bool(n.finalbody) and any(isinstance(a,ast.Name) and a.id.startswith('_g1_') for stmt in n.finalbody for a in ast.walk(stmt))
        observation_except=any(h.name=='_g1_exception' for h in n.handlers)
        if observation_final or observation_except:
            out=[]
            for stmt in n.body+(n.orelse if observation_except else []):
                x=self.visit(stmt);out.extend(x if isinstance(x,list) else [x] if x is not None else [])
            return out
        return self.generic_visit(n)
on_results={}
for path in paths:
    before=ast.parse(subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT))
    after=On().visit(ast.parse((ROOT/path).read_text()))
    same=dump(before)==dump(after)
    on_results[path]=same
    if not same:
        import difflib
        print('ON '+path)
        print(''.join(difflib.unified_diff(ast.unparse(before).splitlines(True),ast.unparse(after).splitlines(True)))[:7000])
print('ON',json.dumps(on_results,indent=2))

assert all(results.values()) and all(on_results.values())
```
