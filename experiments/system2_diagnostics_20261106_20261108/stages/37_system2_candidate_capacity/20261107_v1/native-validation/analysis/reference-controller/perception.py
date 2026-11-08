"""Resident batched semantic proposals from RGB, calibrated head rays only."""
import os
import numpy as np
import torch
from PIL import Image
from transformers import AutoProcessor,AutoModelForZeroShotObjectDetection,CLIPProcessor,CLIPModel
PROMPT='basket. wrist watch. toy car. camera. mobile phone. toy truck.'
HEIGHT={'basket':.07,'watch':.025,'toy_car':.04,'camera':.055,'phone':.025,'garage':.055}
def category(label):
 if 'basket' in label:return 'basket'
 if 'watch' in label:return 'watch'
 if 'truck' in label:return 'garage'
 if 'car' in label and 'camera' not in label:return 'toy_car'
 if 'camera' in label:return 'camera'
 if 'phone' in label:return 'phone'
 return None

def ray(uv,z):
 u,v=uv;f=640*10/22.212;up=-(v-240)/f;d=(z-1.308)/(.5*up-.8660254037844386)
 return np.array([d*(u-320)/f,-.41+d*(.8660254037844386*up+.5),z])
def iou(a,b):
 inter=np.maximum(0,np.minimum(a[2:],b[2:])-np.maximum(a[:2],b[:2])).prod()
 return inter/max(1,(a[2:]-a[:2]).prod()+(b[2:]-b[:2]).prod()-inter)
QUERIES={'basket':'basket.','watch':'wrist watch.','toy_car':'toy car. wooden toy car.','camera':'camera. black camera.','pen':'pen.','garage':'rabbit figurine.'}
HEIGHT.update(pen=.012)
class Reader:
 def __init__(self):
  root=os.environ['CLASSIFY_DINO_MODEL'];self.proc=AutoProcessor.from_pretrained(root,local_files_only=True)
  self.net=AutoModelForZeroShotObjectDetection.from_pretrained(root,local_files_only=True).to('cuda').eval()
  cliproot=os.environ['CLASSIFY_CLIP_MODEL'];self.clipproc=CLIPProcessor.from_pretrained(cliproot,local_files_only=True)
  self.clip=CLIPModel.from_pretrained(cliproot,local_files_only=True).to('cuda').eval()
  self.classes=['camera','toy_car','watch','pen','garage','robot','table']
  descriptions=[
   ['a camera','a small black camera','a digital camera','a compact camera'],
   ['a toy car','a toy racing car','a miniature car','a small wooden car'],
   ['a wrist watch','a watch with a strap','an analog wristwatch','a wrist watch with a band'],
   ['a pen','a writing pen','a ballpoint pen','a fountain pen'],
   ['a rabbit toy figurine','a rabbit figurine','a small toy rabbit','a bunny figure'],
   ['a robot gripper','a robot arm','a robotic hand','a metal robot gripper'],
   ['an empty wooden table','a wooden tabletop','a table surface','a bare wooden table'],
  ]
  texts=['a photo of '+name for group in descriptions for name in group]
  inputs=self.clipproc(text=texts,padding=True,return_tensors='pt').to('cuda')
  with torch.inference_mode():features=self.clip.get_text_features(**inputs)
  features=features/features.norm(dim=-1,keepdim=True)
  self.text_features=features.reshape(len(self.classes),4,-1).mean(dim=1)
  self.text_features=self.text_features/self.text_features.norm(dim=-1,keepdim=True)
 def read_batch(self,images,states,recovery_flags=None,temporal_sources=None):
  recovery_flags=[False]*len(images) if recovery_flags is None else recovery_flags
  temporal_sources=[None]*len(images) if temporal_sources is None else temporal_sources
  jobs=[];result=[[] for _ in images]
  for i,rgb in enumerate(images):
   for cat,text in QUERIES.items():
    crop=rgb if cat=='basket' else rgb[205:(395 if recovery_flags[i] else 325),75:565]
    jobs.append((i,cat,text,Image.fromarray(crop)))
  for begin in range(0,len(jobs),8):
   batch=jobs[begin:begin+8]
   inp=self.proc(images=[j[3] for j in batch],text=[j[2] for j in batch],padding=True,return_tensors='pt').to('cuda')
   with torch.inference_mode():out=self.net(**inp)
   pp=self.proc.post_process_grounded_object_detection(out,inp.input_ids,threshold=.18,text_threshold=.18,target_sizes=[(j[3].height,j[3].width) for j in batch])
   for (idx,cat,query,im),p in zip(batch,pp):
    for box,score in zip(p['boxes'].detach().cpu().numpy(),p['scores'].detach().cpu().numpy()):
     if cat!='basket':box=box+np.array([75,205,75,205])
     wh=box[2:]-box[:2]
     if cat!='basket' and (wh.max()>105 or wh.prod()>6000):continue
     center=(box[:2]+box[2:])/2;xyz=ray(center,.765+HEIGHT[cat]/2)
     if abs(xyz[0])>.46 or (cat!='basket' and not (-.45 if recovery_flags[idx] else -.255)<xyz[1]<.015):continue
     result[idx].append(dict(category=cat,box=box,score=float(score),xyz=xyz,label=query))
  from .foreground import boxes,covered
  for i,rgb in enumerate(images):
   foreground_boxes=boxes(rgb,ymax=395 if recovery_flags[i] else 325)
   instances=[x for x in result[i] if x['category']!='basket']
   for box in foreground_boxes:
    if any(covered(x['box'],box) for x in instances):continue
    xyz=ray((box[:2]+box[2:])/2,.785)
    if abs(xyz[0])<.46 and (-.45 if recovery_flags[i] else -.255)<xyz[1]<.015:
     result[i].append(dict(category='camera',box=box,score=0.,xyz=xyz,label='RGB foreground'))
  outputs=[]
  for idx,items in enumerate(result):
   kept=[]
   for x in sorted(items,key=lambda x:-x['score']):
    if not any(iou(x['box'],y['box'])>.4 for y in kept):kept.append(x)
   source=temporal_sources[idx]
   if source is not None:
    for box in source.boxes(images[idx]):
     xyz=ray((box[:2]+box[2:])/2,.765+HEIGHT[source.category]/2)
     if abs(xyz[0])<.46 and -.45<xyz[1]<.015:
      kept.append(dict(category=source.category,box=box,score=0.,xyz=xyz,label='RGB temporal change'))
   outputs.append(kept)
  from .robot_mask import robot_mask,robot_fraction
  self.last_robot_exclusions=[]
  for i,items in enumerate(outputs):
   mask=robot_mask(states[i],images[i].shape)
   excluded=[x for x in items if x['category']!='basket' and robot_fraction(mask,x['box'])>0.]
   self.last_robot_exclusions.append([dict(category=x['category'],box=x['box'],robot_fraction=robot_fraction(mask,x['box'])) for x in excluded])
   outputs[i]=[x for x in items if x['category']=='basket' or robot_fraction(mask,x['box'])==0.]
  proposals=[(i,x) for i,items in enumerate(outputs) for x in items if x['category']!='basket']
  if proposals:
   crops=[]
   for i,x in proposals:
    box=np.asarray(x['box']);center=(box[:2]+box[2:])/2;size=max(box[2:]-box[:2])*1.25
    xy=np.maximum(0,center-size/2).astype(int);zw=np.minimum([640,480],center+size/2).astype(int)
    crops.append(Image.fromarray(images[i]).crop((*xy,*zw)))
   references=[]
   for source in temporal_sources:
    if source is not None and source.feature is None and not any(source is x for x in references):
     references.append(source);crops.append(Image.fromarray(source.crop))
   feature_batches=[]
   for begin in range(0,len(crops),32):
    inputs=self.clipproc(images=crops[begin:begin+32],return_tensors='pt').to('cuda')
    with torch.inference_mode():features=self.clip.get_image_features(**inputs)
    feature_batches.append(features/features.norm(dim=-1,keepdim=True))
   normalized=torch.cat(feature_batches,dim=0)
   normalized_cpu=normalized.detach().cpu().numpy()
   for source,feature in zip(references,normalized_cpu[len(proposals):]):source.feature=feature.copy()
   similarities=normalized[:len(proposals)]@self.text_features.T
   for (i,x),sim,feature in zip(proposals,similarities.detach().cpu().numpy(),normalized_cpu):
    old=x['category'];semantic=sim.copy()
    # A weak detector vote resolves ambiguous crops; strong CLIP evidence still wins.
    if x['label'] not in ('RGB foreground','RGB temporal change'):
     semantic[self.classes.index(old)]+=.05*x['score']
    cat=self.classes[int(semantic.argmax())]
    if x['label']=='RGB temporal change':
     source=temporal_sources[i];match=float(feature@source.feature)
     accepted=source.supports_category(sim,match,self.classes)
     x['temporal_source_cosine']=match;x['temporal_source_category']=source.category
     x['temporal_accepted']=accepted
     cat=source.category if accepted else 'table'
    x['dino_category']=old;x['clip_similarities']=sim;x['semantic_fusion_scores']=semantic;x['category']=cat
    x['score']=float(sim[self.classes.index(cat)]);x['xyz']=ray((x['box'][:2]+x['box'][2:])/2,.765+HEIGHT.get(cat,.04)/2)
  from .grasp_shape import grasp
  filtered=[];self.last_basket_exclusions=[[] for _ in images]
  for image_idx,items in enumerate(outputs):
   baskets=[x['box'] for x in items if x['category']=='basket']
   accepted=[]
   for obj in items:
    if obj['category'] in ['robot','table']:continue
    if obj['category']!='basket':
     box=np.asarray(obj['box']);near=[b for b in baskets if np.all(np.minimum(box[2:]+6,b[2:])-np.maximum(box[:2]-6,b[:2])>0)]
     if near:
      obj['current_rgb_basket_boxes']=near
      geometry=grasp(images[image_idx],obj)
      if geometry is None:
       self.last_basket_exclusions[image_idx].append(dict(category=obj['category'],box=obj['box'],basket_boxes=near,reason='fewer than8 source silhouette pixels outside current RGB basket boxes'))
       continue
      contact,q,shape=geometry
      obj['current_rgb_grasp']=dict(contact=contact,quaternion=q,shape=shape)
    accepted.append(obj)
   filtered.append(accepted)
  return filtered
