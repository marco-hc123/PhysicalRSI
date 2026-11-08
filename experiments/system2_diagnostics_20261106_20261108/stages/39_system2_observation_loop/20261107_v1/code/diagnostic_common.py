"""Bounded diagnostic serialization, never used to construct policy inputs."""
import enum, math, time, json

def safe(v, depth=0):
    if depth > 5: return {'type':type(v).__name__,'truncated':True}
    if v is None or isinstance(v,(str,bool,int)): return v
    if isinstance(v,float): return v if math.isfinite(v) else str(v)
    if isinstance(v,enum.Enum): return {'name':v.name,'value':safe(v.value,depth+1)}
    if isinstance(v,dict):return {str(k):safe(x,depth+1) for k,x in list(v.items())[:60]}
    if isinstance(v,(list,tuple)):return [safe(x,depth+1) for x in v[:100]]
    if hasattr(v,'detach'):v=v.detach()
    if hasattr(v,'shape'):
        shape=list(v.shape);n=math.prod(shape)
        if n>100:return {'shape':shape,'dtype':str(getattr(v,'dtype','unknown')),'values_omitted':True}
        if hasattr(v,'cpu'):v=v.cpu()
        return safe(v.tolist(),depth+1)
    return {'type':type(v).__name__,'text':str(v)[:300]}

def append(path, record):
    record=dict(record);record.setdefault('monotonic_ns',time.monotonic_ns())
    with path.open('a') as f:f.write(json.dumps(safe(record),allow_nan=False)+'\n')
