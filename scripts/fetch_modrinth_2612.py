import json, re, hashlib, urllib.parse, urllib.request, zipfile, time
from pathlib import Path

GAME='26.1.2'; LOADER='fabric'; OUT=Path('mods-26.1.2'); OUT.mkdir(exist_ok=True)
requested=[
('BadOptimizations',['BadOptimizations','badoptimizations']),('Better Block Entities',['Better Block Entities','better-block-entities','bbe']),
('BetterF3',['BetterF3','betterf3']),('Cloth Config API',['Cloth Config API','cloth-config']),('Drippy Loading Screen',['Drippy Loading Screen','drippy-loading-screen']),
('Entity Model Features',['Entity Model Features','entity-model-features']),('Entity Texture Features',['Entity Texture Features','entitytexturefeatures']),('Fabric API',['Fabric API','fabric-api']),
('FancyMenu',['FancyMenu','fancymenu']),('Fast IP Ping',['Fast IP Ping','fast-ip-ping']),('FerriteCore',['FerriteCore','ferrite-core']),('ImmediatelyFast',['ImmediatelyFast','immediatelyfast']),
('Iris Shaders',['Iris Shaders','iris']),('Konkrete',['Konkrete','konkrete']),('LambDynamicLights',['LambDynamicLights','lambdynamiclights']),('Lithium',['Lithium','lithium']),
('Melody',['Melody','melody']),('More Culling',['More Culling','moreculling']),('Mouse Tweaks',['Mouse Tweaks','mouse-tweaks']),('Reimagined Intro',['Reimagined Intro','reimagined-intro']),
('Sodium Extra',['Sodium Extra','sodium-extra']),('Sodium',['Sodium','sodium']),('WaterMedia',['WaterMedia','watermedia']),('WaterMedia Binaries',['WaterMedia Binaries','watermedia binaries','watermedia-binaries'])]
UA={'User-Agent':'ChatGPT-Modrinth-Pack-Builder/1.0'}
def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=45) as r:return json.load(r)
def norm(s):return re.sub(r'[^a-z0-9]+','',s.lower())
def find_project(label,aliases):
    targets={norm(label),*(norm(a) for a in aliases)}
    for q in aliases:
        url='https://api.modrinth.com/v2/search?'+urllib.parse.urlencode({'query':q,'limit':20,'facets':'[["project_type:mod"]]'})
        hits=get_json(url).get('hits',[])
        for h in hits:
            if norm(h.get('title','')) in targets or norm(h.get('slug','')) in targets:return h
    return None
def versions_for(pid):
    q=urllib.parse.urlencode({'loaders':json.dumps([LOADER]),'game_versions':json.dumps([GAME])})
    return get_json(f'https://api.modrinth.com/v2/project/{pid}/version?{q}')
def choose(vs):
    if not vs:return None
    rank={'release':0,'beta':1,'alpha':2}; br=min(rank.get(v.get('version_type'),9) for v in vs); vs=[v for v in vs if rank.get(v.get('version_type'),9)==br]
    return max(vs,key=lambda v:v.get('date_published',''))
manifest={'game_version':GAME,'loader':LOADER,'source_policy':'Modrinth only','mods':[],'skipped':[],'errors':[]}; done=set(); deps=[]
def download(label,project,ver,direct=True):
    pid=project.get('project_id') or project.get('id')
    if pid in done:return
    files=ver.get('files',[]); f=next((x for x in files if x.get('primary') and x.get('filename','').endswith('.jar')),None) or next((x for x in files if x.get('filename','').endswith('.jar')),None)
    if not f:manifest['errors'].append({'name':label,'reason':'No JAR'});return
    host=urllib.parse.urlparse(f['url']).hostname or ''
    if not (host=='cdn.modrinth.com' or host.endswith('.modrinth.com')):manifest['errors'].append({'name':label,'reason':'non-Modrinth URL rejected'});return
    dest=OUT/f['filename']
    with urllib.request.urlopen(urllib.request.Request(f['url'],headers=UA),timeout=120) as r, open(dest,'wb') as w:
        while True:
            b=r.read(1024*1024)
            if not b:break
            w.write(b)
    actual=hashlib.sha512(dest.read_bytes()).hexdigest(); expected=f.get('hashes',{}).get('sha512')
    if expected and actual.lower()!=expected.lower():raise RuntimeError('hash mismatch '+f['filename'])
    done.add(pid); manifest['mods'].append({'name':label,'project_id':pid,'slug':project.get('slug'),'version':ver.get('version_number'),'version_id':ver.get('id'),'filename':f['filename'],'url':f['url'],'sha512':actual,'direct_request':direct})
    deps.extend(d['project_id'] for d in ver.get('dependencies',[]) if d.get('dependency_type')=='required' and d.get('project_id'))
for label,aliases in requested:
    try:
        p=find_project(label,aliases)
        if not p:manifest['skipped'].append({'name':label,'reason':'No matching Modrinth project'});continue
        v=choose(versions_for(p['project_id']))
        if not v:manifest['skipped'].append({'name':label,'reason':'No Fabric 26.1.2 version on Modrinth'});continue
        download(label,p,v,True)
    except Exception as e:manifest['errors'].append({'name':label,'reason':repr(e)})
    time.sleep(.05)
seen=set()
while deps:
    pid=deps.pop(0)
    if pid in seen or pid in done:continue
    seen.add(pid)
    try:
        p=get_json(f'https://api.modrinth.com/v2/project/{pid}'); v=choose(versions_for(pid))
        if v:download(p.get('title',pid),p,v,False)
        else:manifest['errors'].append({'name':p.get('title',pid),'reason':'Required dependency missing Fabric 26.1.2'})
    except Exception as e:manifest['errors'].append({'name':pid,'reason':repr(e)})
manifest['skipped'] += [{'name':'Floodgate Spigot','reason':'server plugin; bundle restricted to Modrinth mods only'},{'name':'TL Skin & Cape','reason':'not accepted without a Modrinth source'}]
(OUT/'MODRINTH_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile('Minecraft-26.1.2-Fabric-Modrinth-Only.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(OUT.parent))
print(json.dumps(manifest,indent=2))
