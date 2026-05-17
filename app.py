from flask import Flask, render_template, request, redirect, url_for
import sqlite3, uuid
from datetime import datetime, timedelta

app = Flask(__name__)
DB = 'cards.db'

# ====== ИНИЦИАЛИЗАЦИЯ БД ======
def init_db():
    conn = sqlite3.connect(DB)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            about TEXT,
            link_tg TEXT,
            link_wa TEXT,
            link_other TEXT,
            expires_at TEXT NOT NULL
        )
    ''')
    conn.close()

init_db()

# ====== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======
def get_card(card_id):
    conn = sqlite3.connect(DB)
    cur = conn.execute('SELECT * FROM cards WHERE id=?', (card_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        'id': row[0],
        'name': row[1],
        'about': row[2],
        'link_tg': row[3],
        'link_wa': row[4],
        'link_other': row[5],
        'expires_at': row[6]
    }

def delete_card(card_id):
    conn = sqlite3.connect(DB)
    conn.execute('DELETE FROM cards WHERE id=?', (card_id,))
    conn.commit()
    conn.close()

# ====== МАРШРУТЫ ======
@app.route('/', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        card_id = str(uuid.uuid4())[:8]
        name = request.form['name']
        about = request.form.get('about', '')
        link_tg = request.form.get('tg', '')
        link_wa = request.form.get('wa', '')
        link_other = request.form.get('other', '')
        hours = int(request.form['lifetime'])

        # считаем дату истечения
        expires_at = (datetime.now() + timedelta(hours=hours)).isoformat()

        conn = sqlite3.connect(DB)
        conn.execute('INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (card_id, name, about, link_tg, link_wa, link_other, expires_at))
        conn.commit()
        conn.close()

        return redirect(url_for('card', card_id=card_id), code=303)

    return render_template('create.html')

@app.route('/card/<card_id>', methods=['GET', 'POST'])
def card(card_id):
    card_data = get_card(card_id)
    if not card_data:
        return '<h1>Визитка не найдена или истекла</h1>', 404

    # проверяем срок годности
    expires = datetime.fromisoformat(card_data['expires_at'])
    if datetime.now() > expires:
        delete_card(card_id)
        return '<h1>Визитка истекла</h1>', 410

    # генерируем URL для QR-кода через внешний API
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={url_for('card', card_id=card_id, _external=True)}"
    return render_template('card.html', card=card_data, qr_url=qr_url)
    

if __name__ == '__main__':
    app.run(debug=True)
