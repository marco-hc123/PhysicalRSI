"""Render a procedural RGB scene in Isaac Sim; no robot or policy claim."""
from pathlib import Path
import json,time
out=Path('/mnt/data/physical-RSI/result/31_rgb_supplement_20261105/rgb-smoke')
started=time.monotonic()
from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'width':640,'height':480,'renderer':'RaytracedLighting','anti_aliasing':0,'multi_gpu':False,'sync_loads':True,'extra_args':['--/app/settings/persistent=false','--/log/file='+str(out/'kit.log'),'--/app/tokens/cache=/mnt/data/physical-RSI/cache/kit','--/app/tokens/data=/mnt/data/physical-RSI/cache/kit-data']})
try:
 import numpy as np
 from PIL import Image
 from pxr import UsdGeom,UsdLux,UsdShade,Sdf,Gf
 import omni.usd
 import omni.replicator.core as rep
 stage=omni.usd.get_context().get_stage()
 UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
 UsdGeom.SetStageMetersPerUnit(stage,1.0)
 UsdGeom.Xform.Define(stage,'/World')
 def color_material(path,color):
  material=UsdShade.Material.Define(stage,path)
  shader=UsdShade.Shader.Define(stage,path+'/Shader');shader.CreateIdAttr('UsdPreviewSurface')
  shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
  shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(0.65)
  material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
  return material
 def cube(path,pos,scale,color):
  obj=UsdGeom.Cube.Define(stage,path);obj.CreateSizeAttr(1.0)
  obj.AddTranslateOp().Set(Gf.Vec3d(*pos));obj.AddScaleOp().Set(Gf.Vec3d(*scale))
  UsdShade.MaterialBindingAPI.Apply(obj.GetPrim()).Bind(color_material(path+'_Material',color))
 cube('/World/Floor',(0,0,-0.05),(5,5,.1),(.45,.45,.45))
 cube('/World/RedCube',(-.55,0,.3),(.6,.6,.6),(.9,.04,.03))
 sphere=UsdGeom.Sphere.Define(stage,'/World/BlueSphere');sphere.CreateRadiusAttr(.32)
 sphere.AddTranslateOp().Set(Gf.Vec3d(.55,0,.32));UsdShade.MaterialBindingAPI.Apply(sphere.GetPrim()).Bind(color_material('/World/BlueMaterial',(.03,.08,.9)))
 cube('/World/GreenCube',(0,.65,.2),(.4,.4,.4),(.03,.8,.08))
 light=UsdLux.DomeLight.Define(stage,'/World/DomeLight');light.CreateIntensityAttr(1000.0)
 sun=UsdLux.DistantLight.Define(stage,'/World/Sun');sun.CreateIntensityAttr(1500.0);UsdGeom.Xformable(sun.GetPrim()).AddRotateXYZOp().Set(Gf.Vec3f(-35,25,0))
 camera=UsdGeom.Camera.Define(stage,'/World/Camera');camera.CreateFocalLengthAttr(24.0);camera.CreateHorizontalApertureAttr(24.0)
 matrix=Gf.Matrix4d().SetLookAt(Gf.Vec3d(2.3,-3.0,2.2),Gf.Vec3d(0,0,.25),Gf.Vec3d(0,0,1)).GetInverse()
 camera.AddTransformOp().Set(matrix)
 product=rep.create.render_product('/World/Camera',(640,480))
 annotator=rep.AnnotatorRegistry.get_annotator('rgb');annotator.attach([product])
 for _ in range(20):app.update()
 frames=[]
 for index in range(6):
  rep.orchestrator.step(rt_subframes=4,pause_timeline=False)
  for _ in range(3):app.update()
  frame=np.asarray(annotator.get_data())
  if frame.ndim==3 and frame.shape[:2]==(480,640):frames.append(frame.copy())
 if not frames:raise RuntimeError('No camera frame returned')
 rgb=frames[-1][...,:3].astype(np.uint8)
 Image.fromarray(rgb,mode='RGB').save(out/'rgb_scene.png')
 pixels=rgb.astype(np.float32)
 red=(pixels[...,0]>1.4*pixels[...,1])&(pixels[...,0]>1.4*pixels[...,2])&(pixels[...,0]>40)
 blue=(pixels[...,2]>1.4*pixels[...,0])&(pixels[...,2]>1.4*pixels[...,1])&(pixels[...,2]>40)
 green=(pixels[...,1]>1.3*pixels[...,0])&(pixels[...,1]>1.3*pixels[...,2])&(pixels[...,1]>40)
 checks={'shape_correct':list(rgb.shape)==[480,640,3],'nonconstant':float(rgb.std())>10,'red_pixels':int(red.sum()),'blue_pixels':int(blue.sum()),'green_pixels':int(green.sum())}
 passed=checks['shape_correct'] and checks['nonconstant'] and min(checks['red_pixels'],checks['blue_pixels'],checks['green_pixels'])>50
 stage.GetRootLayer().Export(str(out/'procedural_scene.usda'))
 result={'passed':passed,'scope':'Procedural Isaac Sim RGB rendering smoke test','renderer':'RaytracedLighting','resolution':[640,480],'frames_received':len(frames),'pixel_min':int(rgb.min()),'pixel_max':int(rgb.max()),'pixel_std':float(rgb.std()),'checks':checks,'elapsed_seconds':time.monotonic()-started,'robot_task_executed':False,'api_calls':0}
 (out/'render_result.json').write_text(json.dumps(result,indent=2))
 print('RGB_SMOKE_RESULT',json.dumps(result),flush=True)
 if not passed:raise RuntimeError('Rendered image failed pixel checks')
finally:
 app.close()
