# Проверка карточки релиза в настоящем браузере.
import json, subprocess, time, shutil, os, datetime
from playwright.sync_api import sync_playwright
import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T='/tmp/mamen-test-site'; PORT=8792
def build(mut):
    shutil.rmtree(T,ignore_errors=True); shutil.copytree(ROOT,T,ignore=shutil.ignore_patterns('.git','docs'))
    d=json.load(open(T+'/data/site.json')); mut(d); json.dump(d,open(T+'/data/site.json','w'),ensure_ascii=False)
    subprocess.run(['node',ROOT+'/src/build.mjs',T],check=True,stdout=subprocess.DEVNULL)
def msk(dt):  # дата и время по Москве с точностью до минуты
    m=dt.astimezone(datetime.timezone(datetime.timedelta(hours=3))); return m.strftime('%Y-%m-%d'), m.strftime('%H:%M')
srv=None
def serve():
    global srv
    if srv: srv.terminate(); srv.wait()
    srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--directory',T],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(0.8)
def state(pg): return pg.evaluate("(()=>{const e=document.querySelector('[data-release]'); if(!e) return null; const vis=s=>[...e.querySelectorAll('[data-state=\"'+s+'\"]')].some(x=>x.offsetParent!==null); return {show:e.dataset.show,pending:e.classList.contains('is-pending'),soonVisible:vis('soon'),outVisible:vis('out'),listen:!!e.querySelector('.release__listen') && e.querySelector('.release__listen').offsetParent!==null,presave:e.querySelectorAll('.release__presave a').length}})()")
res=[]
def check(name,cond,info=''): res.append((name,bool(cond),info)); print(('OK  ' if cond else 'FAIL'),name,info)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    def page(skew_ms=0, js=True):
        ctx=b.new_context(viewport={'width':390,'height':844},java_script_enabled=js)
        if skew_ms: ctx.add_init_script(f"(()=>{{const r=Date.now.bind(Date);Date.now=()=>r()+({skew_ms});}})()")
        pg=ctx.new_page(); pg.goto(f'http://localhost:{PORT}/',wait_until='load'); return pg
    # 1. Автопереключение: релиз в ближайшую целую минуту
    now=datetime.datetime.now(datetime.timezone.utc)
    target=(now+datetime.timedelta(seconds=75)).replace(second=0,microsecond=0)
    if (target-now).total_seconds()<25: target+=datetime.timedelta(minutes=1)
    d_,t_=msk(target)
    build(lambda d: d['release'].update(mode='auto',date=d_,time=t_)); serve()
    pg_ok=page(); pg_slow=page(skew_ms=-120000); pg_fast=page(skew_ms=+120000)
    time.sleep(2.2)
    s1,s2,s3=state(pg_ok),state(pg_slow),state(pg_fast)
    check('до релиза: верные часы → «Скоро»', s1['show']=='soon' and s1['soonVisible'] and not s1['listen'] and s1['presave']==2, s1)
    check('до релиза: часы отстают на 2 мин → «Скоро»', s2['show']=='soon', s2)
    check('до релиза: часы спешат на 2 мин → всё равно «Скоро»', s3['show']=='soon', s3)
    wait=(target-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    time.sleep(max(0,wait-1.6)); pre=[state(x)['show'] for x in (pg_ok,pg_slow,pg_fast)]
    check('за ~1,6 с до релиза все ещё «Скоро»', pre==['soon']*3, pre)
    time.sleep(3.4); post=[state(x) for x in (pg_ok,pg_slow,pg_fast)]
    check('через ~1,8 с после релиза все «Новый релиз» без перезагрузки', all(x['show']=='out' and x['listen'] and not x['soonVisible'] for x in post), [x['show'] for x in post])
    pg_new=page(); time.sleep(1.2); s=state(pg_new)
    check('новая загрузка после релиза → «Новый релиз»', s['show']=='out' and s['listen'], s)
    # 2. Без скриптов: видно состояние на момент публикации
    pg_nojs=page(js=False); s=pg_nojs.evaluate("null") if False else None
    vis=pg_nojs.locator('.release').evaluate("e=>getComputedStyle(e).visibility")
    check('скрипты отключены → карточка видна', vis=='visible', vis)
    # 3. Ручные режимы и отсутствующие ссылки
    build(lambda d: d['release'].update(mode='soon',date='2020-01-01')); serve(); s=state(page())
    check('ручной режим «Скоро» при прошедшей дате', s['show']=='soon' and s['presave']==2, s)
    build(lambda d: d['release'].update(mode='out',date='2099-01-01')); serve(); s=state(page())
    check('ручной режим «Новый релиз» при будущей дате', s['show']=='out' and s['listen'], s)
    build(lambda d: d['release'].update(mode='hidden')); serve(); s=state(page())
    check('режим «Скрыта» → карточки нет', s is None, s)
    build(lambda d: d['release'].update(mode='out',listenUrl='')); serve(); s=state(page())
    check('нет мультиссылки → кнопки «Слушать» нет', s['show']=='out' and not s['listen'], s)
    build(lambda d: d['release'].update(mode='soon',presaveVk='',presaveYandex='https://music.yandex.ru/')); serve(); s=state(page())
    check('один пресейв → одна кнопка', s['presave']==1, s)
    build(lambda d: d['release'].update(mode='soon',presaveVk='javascript:alert(1)',presaveYandex='')); serve(); s=state(page())
    check('опасная ссылка отброшена → кнопок пресейва нет', s['presave']==0, s)
    b.close()
srv.terminate()
print('ИТОГО:',sum(1 for r in res if r[1]),'из',len(res))
