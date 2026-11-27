from flask import Flask, jsonify, request, render_template, send_from_directory
from backend.engine import InventoryEngine, OUT
import os
app=Flask(__name__,template_folder='frontend/templates',static_folder='frontend/static')
engine=InventoryEngine(); engine.load_all()
@app.get('/')
def home(): return render_template('index.html')
@app.get('/api/summary')
def summary(): return jsonify(engine.summary())
@app.get('/api/branches')
def branches(): return jsonify(list(engine.branches.values()))
@app.get('/api/stock')
def stock(): return jsonify(engine.stock_rows(request.args.get('branch',''),request.args.get('q',''),request.args.get('status','')))
@app.get('/api/transfers')
def transfers(): return jsonify(engine.transfers)
@app.get('/api/reorders')
def reorders(): return jsonify([dict(x) for x in engine.reorders.values() if x['open']])
@app.get('/api/reports/<name>')
def reports(name):
    if name not in ['transfers.csv','reorders.csv','stock_position.csv','errors.csv']:return jsonify({'error':'Unknown report'}),404
    return send_from_directory(OUT,name,as_attachment=True) if os.path.exists(os.path.join(OUT,name)) else (jsonify({'error':'Run replenishment first'}),404)
@app.post('/api/replenish')
def replenish():
    data=request.get_json(silent=True) or {}; dt=data.get('date')
    if not dt:return jsonify({'error':'Date is required'}),400
    try:engine.replenish(dt);engine.write_reports();return jsonify({'message':'Replenishment completed','summary':engine.summary()})
    except Exception as e:return jsonify({'error':str(e)}),400
@app.post('/api/post-sales')
def post_sales():
    dt=(request.get_json(silent=True) or {}).get('date')
    if not dt:return jsonify({'error':'Date is required'}),400
    engine.post_sales(dt);engine.write_reports();return jsonify({'message':f'Sales posted for {dt}','summary':engine.summary()})
@app.post('/api/receive')
def receive():
    d=request.get_json(silent=True) or {}; rid=d.get('reorder_id');dt=d.get('date')
    if not rid or not dt:return jsonify({'error':'Reorder ID and date are required'}),400
    ok=engine.receive(rid,dt);engine.write_reports()
    return (jsonify({'message':'Supplier delivery received','summary':engine.summary()}) if ok else jsonify({'error':'Unknown or closed reorder ID'})),(200 if ok else 400)
@app.post('/api/run-sample')
def run_sample():
    engine.reset();engine.process_commands();return jsonify({'message':'Sample command sequence executed','summary':engine.summary()})
@app.post('/api/reset')
def reset():
    engine.reset();engine.load_all();return jsonify({'message':'Data restored to original sample state','summary':engine.summary()})
if __name__=='__main__':app.run(debug=True,port=5000)
