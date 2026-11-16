import sys, asyncio, subprocess, time
from playwright.sync_api import sync_playwright
PORT=8791
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--directory','.'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1)
tag=sys.argv[1] if len(sys.argv)>1 else 'v1'
jobs=[('home-390',390,844,''),('home-320',320,640,''),('home-768',768,1024,''),('home-1440',1440,900,''),('home-1024',1024,768,''),
      ('about-390',390,844,'about/'),('about-1440',1440,900,'about/'),('contact-390',390,844,'contact/'),('contact-1440',1440,900,'contact/')]
only=sys.argv[2].split(',') if len(sys.argv)>2 else None
try:
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        for name,w,h,path in jobs:
            if only and name not in only: continue
            ctx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=2)
            pg=ctx.new_page(); msgs=[]
            pg.on('console',lambda m: msgs.append(m.type+': '+m.text) if m.type in('error','warning') else None)
            pg.on('pageerror',lambda e: msgs.append('pageerror: '+str(e)))
            pg.on('requestfailed',lambda r: msgs.append('failed: '+r.url))
            pg.goto(f'http://localhost:{PORT}/{path}',wait_until='networkidle')
            pg.evaluate('document.fonts.ready')
            pg.wait_for_timeout(300)
            hh=pg.evaluate('document.documentElement.scrollHeight'); ow=pg.evaluate('document.documentElement.scrollWidth')
            pg.screenshot(path=f'shots/{name}-{tag}.png',full_page=True)
            print(name,'height',hh,'scrollWidth',ow,'viewport',w,msgs)
            ctx.close()
        b.close()
finally:
    srv.terminate()
