import random
import math
from flask import Flask, render_template, request, jsonify, make_response
from fpdf import FPDF

app = Flask(__name__)

# --- Helper Functions ---
def get_prime_factorization(num):
    factors = {}
    divisor = 2
    n = abs(int(num))
    if n <= 1:
        return {n: 1}
    while n > 1:
        if n % divisor == 0:
            factors[divisor] = factors.get(divisor, 0) + 1
            n /= divisor
        else:
            divisor += 1
    return factors

def format_factorization(factors):
    if not factors:
        return '1'
    return ' × '.join([f"{base}<sup>{exp}</sup>" if exp > 1 else str(base) for base, exp in factors.items()])

def generate_factor_tree_text(num):
    if num <= 1:
        return f'<div class="math-calculation"><p>Faktorisasi {num}: {num}</p></div>'
    factors = get_prime_factorization(num)
    return f'<div class="math-calculation"><strong>Pohon Faktor {num}:</strong><br>Faktorisasi Prima: {format_factorization(factors)}</div>'

def simple_numeric_answer(solution_text):
    import re
    matches = re.findall(r'<strong>(.*?)<\/strong>', solution_text)
    if not matches:
        return None
    last_match = matches[-1]
    # Clean up the match
    cleaned = re.sub(r'<sup[^>]*>.*?<\/sup>', '', last_match)
    cleaned = re.sub(r'<sup>', '^', cleaned)
    cleaned = re.sub(r'<\/sup>', '', cleaned)
    cleaned = cleaned.replace('&frasl;', '/')
    return cleaned.split(' ')[0]

studyData = {
    # Data has been moved inside the app.py file
    'grade5': {
        'deret': { 'id': 'deret', 'title': 'Deret Bilangan', 'theory': "Deret aritmatika adalah barisan bilangan dengan selisih yang sama. Untuk menjumlahkannya dengan cepat, gunakan rumus: <strong>Jumlah = (Banyak Bilangan / 2) * (Bilangan Awal + Bilangan Akhir)</strong>.", 'exampleProblem': "Berapakah jumlah bilangan dari 10 sampai 30?", 'exampleSolution': """<div class="text-sm"><p class="step-heading">1. Hitung Banyak Bilangan (n)</p><p>n = (Akhir - Awal) + 1 = (30 - 10) + 1 = <strong>21</strong></p><p class="step-heading">2. Hitung Jumlah</p><p>Jumlah = (21 / 2) * (10 + 30) = 10.5 * 40 = <strong>420</strong></p></div>""", 'variations':[{ 'id': 'sum_series', 'interactiveInputs': [{ 'id': 'start', 'randomRanges': {'mudah':[1,20], 'sedang':[21,50], 'sulit':[51,100]} }, { 'id': 'end', 'randomRanges': {'mudah':[21,50], 'sedang':[51,200], 'sulit':[201,500]} }], 'generateProblem': lambda v: f"Jumlah bilangan asli dari {v['start']} sampai {v['end']}?", 'generateSolution': lambda v: (lambda n, t: f'<div class="text-sm"><p class="step-heading">1. Pahami</p><p>Kita diminta untuk menjumlahkan semua bilangan secara berurutan mulai dari {v["start"]} hingga {v["end"]}.</p><p class="step-heading">2. Konsep</p><p>Gunakan rumus deret: J = (n/2) * (Awal+Akhir).</p><p class="step-heading">3. Hitung</p><p>n = {v["end"]}-{v["start"]}+1 = <strong>{n}</strong>.<br>J = ({n}/2) * ({v["start"]}+{v["end"]}) = <strong>{t}</strong>.</p><p class="step-heading">4. Simpulan</p><p class="font-semibold">Jumlahnya adalah <strong>{t}</strong>.</p></div>')(v['end'] - v['start'] + 1, ((v['end'] - v['start'] + 1) / 2) * (v['start'] + v['end'])) }] },
        # All other topics for Grade 5...
    },
    'grade6': {
        'bilanganBulat': { 'id': 'bilanganBulat', 'title': 'Bilangan Bulat', 'theory': "Penjumlahan dengan bilangan negatif sama dengan pengurangan. Pengurangan dengan bilangan negatif sama dengan penjumlahan. Contoh: 5 + (-3) = 5 - 3 = 2. Dan 5 - (-3) = 5 + 3 = 8.", 'exampleProblem': "Hasil dari -7 + 15?", 'exampleSolution': """<div class="text-sm"><p>Bayangkan kamu punya hutang 7, lalu kamu bayar 15. Kamu akan punya kembalian. Kembaliannya adalah 15 - 7 = <strong>8</strong>.</p></div>""", 'variations':[{ 'id': 'ops_bilangan_bulat', 'interactiveInputs': [ { 'id': 'bilA', 'randomRanges': {'mudah':[-10,10], 'sedang':[-25,25], 'sulit':[-50,50]} }, { 'id': 'bilB', 'randomRanges': {'mudah':[-10,10], 'sedang':[-25,25], 'sulit':[-50,50]} } ], 'generateProblem': lambda v: f"Hasil dari {v['bilA']} + ({v['bilB']})?", 'generateSolution': lambda v: (lambda r: f'<div class="text-sm"><p class="step-heading">1. Pahami</p><p>Kita menjumlahkan {v["bilA"]} dengan bilangan negatif {v["bilB"]}.</p><p class="step-heading">2. Konsep</p><p>Aturan: "+ bertemu -" menjadi "-". Jadi, {v["bilA"]} + ({v["bilB"]}) sama dengan {v["bilA"]} - {abs(v["bilB"])}.</p><p class="step-heading">3. Hitung</p><p class="math-calculation">{v["bilA"]} - {abs(v["bilB"])} = <strong>{r}</strong></p><p class="step-heading">4. Simpulan</p><p class="font-semibold">Hasilnya <strong>{r}</strong>.</p></div>')(v['bilA'] + v['bilB']) }] },
        # All other topics for Grade 6...
    }
}


@app.route('/')
def index():
    return render_template('index.html', study_data=studyData)

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    settings = request.json
    kelas = f"grade{settings['kelas']}"
    jumlah = int(settings['jumlah'])
    kesulitan = settings['kesulitan']

    topic_pool = studyData[kelas]
    topic_keys = list(topic_pool.keys())
    random.shuffle(topic_keys)

    question_recipes = []
    for i in range(jumlah):
        topic_key = topic_keys[i % len(topic_keys)]
        topic = topic_pool[topic_key]
        variation = random.choice(topic['variations'])
        vars = {}
        for inp in variation['interactiveInputs']:
            if 'randomRanges' in inp:
                range_ = inp['randomRanges'][kesulitan]
                vars[inp['id']] = random.randint(range_[0], range_[1])
            elif 'randomDataConfig' in inp:
                cfg = inp['randomDataConfig']
                d = set()
                source = cfg.get('from', [])
                count = random.randint(cfg['count'][0], cfg['count'][1])
                if source:
                    while len(d) < count:
                        d.add(random.choice(source))
                else:
                    while len(d) < count:
                        d.add(random.randint(cfg['range'][0], cfg['range'][1]))
                vars[inp['id']] = ','.join(map(str, d))

        question_recipes.append({
            'topicKey': topic_key,
            'variationId': variation['id'],
            'vars': vars
        })

    return jsonify(question_recipes)

@app.route('/generate_question', methods=['POST'])
def generate_question():
    recipe = request.json
    kelas = f"grade{recipe['kelas']}"
    topic = studyData[kelas][recipe['topicKey']]
    variation = next((v for v in topic['variations'] if v['id'] == recipe['variationId']), None)

    if not variation:
        return jsonify({'error': 'Variation not found'}), 404

    question_text = variation['generateProblem'](recipe['vars'])
    solution_text = variation['generateSolution'](recipe['vars'])
    correct_answer = simple_numeric_answer(solution_text)

    return jsonify({
        'questionText': question_text,
        'solutionText': solution_text,
        'correctAnswer': correct_answer,
        'topicTitle': topic['title']
    })

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    data = request.json

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)

    pdf.set_font_size(24)
    pdf.cell(0, 10, 'Hasil Ujian Matematika', 0, 1, 'C')
    pdf.set_font_size(12)
    pdf.cell(0, 10, f"Skor: {data['score']}", 0, 1, 'C')
    pdf.cell(0, 10, data['summary'], 0, 1, 'C')
    pdf.ln(10)

    pdf.set_font_size(16)
    pdf.cell(0, 10, 'Tinjauan Jawaban', 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    for i, q in enumerate(data['questions']):
        user_answer = data['userAnswers'][i] or '(Tidak dijawab)'
        is_correct = user_answer.replace(',', '.') == q['correctAnswer']

        pdf.set_font('DejaVu', 'B', 12)
        pdf.multi_cell(0, 5, f"{i+1}. {q['questionText']}")

        pdf.set_font('DejaVu', '', 12)
        pdf.text(pdf.get_x() + 5, pdf.get_y() + 5, "Jawabanmu: ")
        pdf.set_text_color(255, 0, 0) if not is_correct else pdf.set_text_color(0, 128, 0)
        pdf.text(pdf.get_x() + 30, pdf.get_y() + 5, user_answer)

        pdf.set_text_color(0, 0, 0)
        pdf.text(pdf.get_x() + 70, pdf.get_y(), "| Jawaban Benar: ")
        pdf.set_text_color(0, 128, 0)
        pdf.text(pdf.get_x() + 110, pdf.get_y(), q['correctAnswer'])

        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        pdf.set_font('DejaVu', 'B', 12)
        pdf.cell(0, 5, "Pembahasan:")
        pdf.ln(5)

        pdf.set_font('DejaVu', '', 10)
        solution_clean = q['solutionText'].replace('<div class="text-sm">', '').replace('</div>', '').replace('<p class="step-heading">', '\n').replace('</p>', '').replace('<br>', '\n').replace('<strong>', '').replace('</strong>', '').replace('<p class="font-semibold">', '').replace('<p>', '').replace('&frasl;', '/').replace('<sup>', '^').replace('</sup>', '')
        pdf.multi_cell(0, 5, solution_clean)
        pdf.ln(5)

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers.set('Content-Disposition', 'attachment', filename='Hasil_Ujian_Matematika.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response

if __name__ == '__main__':
    app.run(debug=True)