from flask import Flask, render_template, request, jsonify, send_file
import sqlite3, json, os, io
from datetime import datetime

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), 'vanshawali.db')

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = db()
    c.execute('''CREATE TABLE IF NOT EXISTS family (
        id INTEGER PRIMARY KEY CHECK (id=1), title TEXT, family_name TEXT,
        village TEXT, police_station TEXT, district TEXT, state TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        father_id INTEGER, mother_id INTEGER, spouse_name TEXT,
        relation TEXT, birth_year TEXT, notes TEXT, created_at TEXT,
        FOREIGN KEY(father_id) REFERENCES people(id),
        FOREIGN KEY(mother_id) REFERENCES people(id)
    )''')
    if c.execute('SELECT COUNT(*) FROM family').fetchone()[0] == 0:
        c.execute('INSERT INTO family(id,title,family_name,village,police_station,district,state) VALUES(1,?,?,?,?,?,?)',
                  ('वंशावली', '', '', '', '', '', ''))
    c.commit(); c.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/print')
def print_page():
    return render_template('print.html')

@app.get('/api/family')
def get_family():
    c=db(); row=c.execute('SELECT * FROM family WHERE id=1').fetchone(); c.close()
    return jsonify(dict(row))

@app.put('/api/family')
def save_family():
    d=request.get_json(force=True)
    c=db(); c.execute('''UPDATE family SET title=?,family_name=?,village=?,police_station=?,district=?,state=? WHERE id=1''',
        (d.get('title',''),d.get('family_name',''),d.get('village',''),d.get('police_station',''),d.get('district',''),d.get('state','')))
    c.commit(); c.close(); return jsonify(ok=True)

@app.get('/api/people')
def get_people():
    c=db(); rows=c.execute('SELECT * FROM people ORDER BY id').fetchall(); c.close()
    return jsonify([dict(r) for r in rows])

@app.post('/api/people')
def add_person():
    d=request.get_json(force=True)
    name=(d.get('name') or '').strip()
    if not name: return jsonify(error='नाम आवश्यक है'),400
    c=db()
    c.execute('''INSERT INTO people(name,father_id,mother_id,spouse_name,relation,birth_year,notes,created_at)
                 VALUES(?,?,?,?,?,?,?,?)''',
              (name,d.get('father_id') or None,d.get('mother_id') or None,d.get('spouse_name',''),
               d.get('relation',''),d.get('birth_year',''),d.get('notes',''),datetime.now().isoformat(timespec='seconds')))
    c.commit(); pid=c.execute('SELECT last_insert_rowid()').fetchone()[0]; c.close()
    return jsonify(id=pid)

def creates_cycle(c, pid, parent_id):
    if not parent_id: return False
    seen=set(); cur=parent_id
    while cur:
        if cur==pid: return True
        if cur in seen: return True
        seen.add(cur)
        row=c.execute('SELECT father_id FROM people WHERE id=?',(cur,)).fetchone()
        cur=row[0] if row else None
    return False

@app.put('/api/people/<int:pid>')
def update_person(pid):
    d=request.get_json(force=True); name=(d.get('name') or '').strip()
    if not name: return jsonify(error='नाम आवश्यक है'),400
    c=db()
    for key in ('father_id','mother_id'):
        val=d.get(key) or None
        if val and int(val)==pid: return jsonify(error='व्यक्ति स्वयं का माता/पिता नहीं हो सकता'),400
        if val and creates_cycle(c,pid,int(val)): return jsonify(error='वंशावली में cycle बन रहा है'),400
    c.execute('''UPDATE people SET name=?,father_id=?,mother_id=?,spouse_name=?,relation=?,birth_year=?,notes=? WHERE id=?''',
              (name,d.get('father_id') or None,d.get('mother_id') or None,d.get('spouse_name',''),
               d.get('relation',''),d.get('birth_year',''),d.get('notes',''),pid))
    c.commit(); c.close(); return jsonify(ok=True)

@app.delete('/api/people/<int:pid>')
def delete_person(pid):
    c=db()
    child=c.execute('SELECT id FROM people WHERE father_id=? OR mother_id=? LIMIT 1',(pid,pid)).fetchone()
    if child:
        c.close(); return jsonify(error='पहले इस व्यक्ति से जुड़े बच्चों के parent संबंध हटाएँ'),400
    c.execute('DELETE FROM people WHERE id=?',(pid,)); c.commit(); c.close(); return jsonify(ok=True)

@app.post('/api/reset')
def reset():
    c=db(); c.execute('DELETE FROM people'); c.commit(); c.close(); return jsonify(ok=True)

@app.get('/api/export')
def export_data():
    c=db(); family=dict(c.execute('SELECT * FROM family WHERE id=1').fetchone()); people=[dict(r) for r in c.execute('SELECT * FROM people ORDER BY id')]; c.close()
    data=json.dumps({'family':family,'people':people},ensure_ascii=False,indent=2).encode('utf-8')
    return send_file(io.BytesIO(data),as_attachment=True,download_name='vanshawali-backup.json',mimetype='application/json')

@app.post('/api/import')
def import_data():
    d=request.get_json(force=True); family=d.get('family',{}); people=d.get('people',[])
    c=db(); c.execute('DELETE FROM people')
    c.execute('UPDATE family SET title=?,family_name=?,village=?,police_station=?,district=?,state=? WHERE id=1',
              (family.get('title','वंशावली'),family.get('family_name',''),family.get('village',''),family.get('police_station',''),family.get('district',''),family.get('state','')))
    for p in people:
        c.execute('''INSERT INTO people(id,name,father_id,mother_id,spouse_name,relation,birth_year,notes,created_at)
                     VALUES(?,?,?,?,?,?,?,?,?)''', (p.get('id'),p.get('name',''),p.get('father_id'),p.get('mother_id'),p.get('spouse_name',''),p.get('relation',''),p.get('birth_year',''),p.get('notes',''),p.get('created_at','')))
    c.commit(); c.close(); return jsonify(ok=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
