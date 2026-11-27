import csv, os, shutil
from collections import defaultdict
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
OUT = os.path.join(ROOT, 'output')
os.makedirs(OUT, exist_ok=True)

class InventoryEngine:
    def __init__(self): self.reset()
    def reset(self):
        self.branches={}; self.distances={}; self.skus={}; self.stock={}; self.sales=[]; self.reorders={}; self.transfers=[]; self.reorder_rows=[]; self.positions=[]; self.errors=[]; self.run_seq=0
        for f in os.listdir(OUT):
            p=os.path.join(OUT,f)
            if os.path.isfile(p): os.remove(p)
    def read(self,name):
        with open(os.path.join(DATA,name),newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
    def load_all(self):
        self.branches={r['branch_id']:r for r in self.read('branches.csv')}
        self.distances={(r['from_branch'],r['to_branch']):int(r['distance_km']) for r in self.read('distances.csv')}
        self.skus={r['sku_code']:{**r,'unit_cost':float(r['unit_cost']),'pack_size':int(r['pack_size'])} for r in self.read('skus.csv')}
        self.stock={(r['branch_id'],r['sku_code']):{'min_qty':int(r['min_qty']),'max_qty':int(r['max_qty']),'stock_qty':int(r['stock_qty'])} for r in self.read('stock.csv')}
        self.reorders={r['reorder_id']:{**r,'qty':int(r['qty']),'open':True} for r in self.read('open_reorders.csv')}
        self.sales=self.read('sales.csv')
    def sales_total(self,b,s,start,end):
        return sum(int(x['qty_sold']) for x in self.sales if x['branch_id']==b and x['sku_code']==s and start<=x['sale_date']<=end)
    def has_open(self,b,s): return any(x['open'] and x['branch_id']==b and x['sku_code']==s for x in self.reorders.values())
    def replenish(self,run_date):
        d=date.fromisoformat(run_date); start=(d-timedelta(days=7)).isoformat(); end=(d-timedelta(days=1)).isoformat(); self.run_seq+=1
        opening={k:v['stock_qty'] for k,v in self.stock.items()}; tin=defaultdict(int); tout=defaultdict(int)
        rows=[]
        for (b,s),v in self.stock.items():
            avg=self.sales_total(b,s,start,end)/7
            eff=v['min_qty']*2 if avg>20 else v['min_qty']
            st=v['stock_qty']; status='SHORT' if st<eff else ('SURPLUS' if st>v['max_qty'] else 'OK')
            cover=(st/avg) if avg>0 else float('inf')
            rows.append({'b':b,'s':s,'avg':avg,'eff':eff,'status':status,'cover':cover,'need':max(0,v['max_qty']-st)})
        shorts=[r for r in rows if r['status']=='SHORT']
        shorts.sort(key=lambda r:(r['avg']==0, r['cover'] if r['avg']>0 else 0, r['b'],r['s']))
        for r in shorts:
            b,s=r['b'],r['s']; need=r['need']; sku=self.skus[s]; pack=sku['pack_size']
            sources=[]
            for (sb,ss),sv in self.stock.items():
                if ss==s and sb!=b:
                    surplus=max(0,sv['stock_qty']-sv['max_qty'])
                    dist=self.distances.get((b,sb),self.distances.get((sb,b),10**9))
                    sources.append((dist,sb,surplus))
            sources.sort(key=lambda x:(x[0],x[1]))
            for dist,sb,surplus in sources:
                if need<=0: break
                qty=min(need,surplus); qty=(qty//pack)*pack
                if qty<=0: continue
                value=qty*sku['unit_cost']
                if value<500: continue
                self.stock[(sb,s)]['stock_qty']-=qty; self.stock[(b,s)]['stock_qty']+=qty
                tout[(sb,s)]+=qty; tin[(b,s)]+=qty; need-=qty
                self.transfers.append({'run_date':run_date,'seq':len([x for x in self.transfers if x['run_date']==run_date])+1,'sku_code':s,'from_branch':sb,'to_branch':b,'qty':qty,'distance_km':dist,'value':round(value,2)})
            if need>0:
                if self.has_open(b,s):
                    self.reorder_rows.append({'run_date':run_date,'branch_id':b,'sku_code':s,'remaining_need':need,'reorder_qty':0,'status':'SKIPPED_OPEN_REORDER'})
                else:
                    reorder_qty=((need+pack-1)//pack)*pack
                    rid=f"RO-{max([int(x[3:]) for x in self.reorders] or [0])+1:04d}"
                    self.reorders[rid]={'reorder_id':rid,'branch_id':b,'sku_code':s,'qty':reorder_qty,'raised_date':run_date,'expected_date':'','open':True}
                    self.reorder_rows.append({'run_date':run_date,'branch_id':b,'sku_code':s,'remaining_need':need,'reorder_qty':reorder_qty,'status':'ORDERED'})
        for r in sorted(rows,key=lambda x:(x['b'],x['s'])):
            k=(r['b'],r['s']); self.positions.append({'run_date':run_date,'branch_id':r['b'],'sku_code':r['s'],'effective_min':r['eff'],'max_qty':self.stock[k]['max_qty'],'opening_stock':opening[k],'transfer_in':tin[k],'transfer_out':tout[k],'closing_stock':self.stock[k]['stock_qty'],'avg_daily_sales':round(r['avg'],2),'status':r['status']})
    def receive(self,rid,dt,line_no=""):

        if rid not in self.reorders or not self.reorders[rid]['open']:
            self.errors.append({'line_no':line_no,'command':f'RECEIVE|{rid}|{dt}','reason':'Unknown or already closed reorder ID'}); return False
        r=self.reorders[rid]; k=(r['branch_id'],r['sku_code']); self.stock[k]['stock_qty']+=r['qty']; r['open']=False; return True
    def post_sales(self,dt):
        for x in self.sales:
            if x['sale_date']==dt:
                k=(x['branch_id'],x['sku_code'])
                if k in self.stock:self.stock[k]['stock_qty']=max(0,self.stock[k]['stock_qty']-int(x['qty_sold']))
    def process_commands(self):
        self.load_all()
        with open(os.path.join(DATA,'commands.txt'),encoding='utf-8') as f:
            for ln,line in enumerate(f,1):
                line=line.strip()
                if not line or line.startswith('#'):continue
                p=line.split('|'); cmd=p[0]
                try:
                    if cmd=='REPLENISH':self.replenish(p[1])
                    elif cmd=='RECEIVE':self.receive(p[1],p[2],ln)
                    elif cmd=='POST_SALES':self.post_sales(p[1])
                    elif cmd.startswith('PRINT_'):pass
                    elif not cmd.startswith('LOAD_'):self.errors.append({'line_no':ln,'command':line,'reason':'Unknown command'})
                except Exception as e:self.errors.append({'line_no':ln,'command':line,'reason':str(e)})
        self.write_reports(); return True
    def write_csv(self,name,fields,rows):
        with open(os.path.join(OUT,name),'w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    def write_reports(self):
        self.write_csv('transfers.csv',['run_date','seq','sku_code','from_branch','to_branch','qty','distance_km','value'],self.transfers)
        self.write_csv('reorders.csv',['run_date','branch_id','sku_code','remaining_need','reorder_qty','status'],self.reorder_rows)
        self.write_csv('stock_position.csv',['run_date','branch_id','sku_code','effective_min','max_qty','opening_stock','transfer_in','transfer_out','closing_stock','avg_daily_sales','status'],self.positions)
        self.write_csv('errors.csv',['line_no','command','reason'],self.errors)
    def summary(self):
        total=sum(x['stock_qty'] for x in self.stock.values()); short=0; surplus=0
        for (b,s),v in self.stock.items():
            if v['stock_qty']<v['min_qty']:short+=1
            if v['stock_qty']>v['max_qty']:surplus+=1
        return {'branches':len(self.branches),'products':len(self.skus),'stock_lines':len(self.stock),'total_units':total,'short_lines':short,'surplus_lines':surplus,'open_reorders':sum(x['open'] for x in self.reorders.values()),'transfers':len(self.transfers),'reorder_lines':len(self.reorder_rows),'errors':len(self.errors)}
    def stock_rows(self,branch='',q='',status=''):
        out=[]
        for (b,s),v in self.stock.items():
            if branch and b!=branch:continue
            sku=self.skus.get(s,{})
            if q and q.lower() not in (s+' '+sku.get('description','')).lower():continue
            st='SHORT' if v['stock_qty']<v['min_qty'] else ('SURPLUS' if v['stock_qty']>v['max_qty'] else 'OK')
            if status and st!=status:continue
            out.append({'branch_id':b,'branch_name':self.branches.get(b,{}).get('branch_name',''),'sku_code':s,'description':sku.get('description',''),'stock_qty':v['stock_qty'],'min_qty':v['min_qty'],'max_qty':v['max_qty'],'unit_cost':sku.get('unit_cost',0),'status':st})
        return sorted(out,key=lambda x:(x['branch_id'],x['sku_code']))
    def report(self,name):
        p=os.path.join(OUT,name)
        if not os.path.exists(p):return []
        with open(p,newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
