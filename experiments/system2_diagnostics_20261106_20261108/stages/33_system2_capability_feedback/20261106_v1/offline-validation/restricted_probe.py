def probe(source, scenes, mode='success', memory=None):
    tree=ast.parse(source)
    if any(isinstance(x,(ast.Import,ast.ImportFrom)) for x in ast.walk(tree)):raise ValueError('Unexpected candidate import')
    scope={'__builtins__': SAFE_BUILTINS};exec(compile(tree,'<audited-candidate>','exec'),scope)
    robot=Robot(scenes,mode);mem=copy.deepcopy(memory or {});terminal='returned';err=None;value=None
    signal.setitimer(signal.ITIMER_REAL,2)
    try:value=scope['policy'](robot,mem)
    except ProbeStop as e:terminal='prefix_observed';err=str(e)
    except BudgetStop as e:terminal='budget_exhausted';err=str(e)
    except ProbeTimeout as e:terminal='cpu_timeout';err=str(e)
    except Exception as e:terminal='exception';err=type(e).__name__+': '+str(e)
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    return {'terminal':terminal,'error':err,'return_value':value,'calls':robot.calls,'counts':dict(collections.Counter(x['method'] for x in robot.calls)),'invalid_calls':robot.invalid,'memory_after_in_process':mem,'native_score':None,'scope':'CPU fixture only; no physics, no new robot episode'}
